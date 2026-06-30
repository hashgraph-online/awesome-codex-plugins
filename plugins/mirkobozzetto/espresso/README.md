<div align="center">

# Espresso

![Espresso](espresso-hero.jpeg)

**One install. Full token-saving stack. Works on Claude Code, Codex, and more.**

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)](https://github.com/mirkobozzetto/espresso)

</div>

---

## The Problem

Every AI coding agent produces verbose output by default.
"Sure! I'd be happy to help. Let me walk you through this step by step..."
That's tokens you pay for, time you waste reading, and context window you burn.

Fixing it requires configuring multiple tools, writing rules, setting up hooks.
Most developers don't bother.

## What Espresso Does

Installs once. Detects what you already have. Adds only what's missing.

| What gets configured | Savings | How |
|---------------------|---------|-----|
| **Output rules** | 40-60% | Enforces 120 char lines, forbidden openers/closers, result-first, no filler |
| **Global rules** | context savings | Creates `~/.claude/rules/` — Exa search, clean git, GitNexus, project rules |
| **GitNexus** | fewer file reads | Configures MCP server + auto-reindex hook (if GitNexus binary installed) |
| **Caveman ultra** | ~75% | Sets compressed conversation mode (if Caveman plugin installed) |
| **RTK hook** | 60-90% CLI | Adds CLI output compression hook (if RTK binary installed) |
| **Ponytail** | less code written | Installs the real ponytail plugin: YAGNI ladder, stdlib/native first, no speculative abstraction |

**Detection-first**: Espresso checks what's already configured and skips it.
Never overwrites your existing rules or config. Never installs duplicates.

---

## Before / After

```
Without Espresso:
  Sure! I'd be happy to help you with that. The issue you're
  experiencing is likely caused by a misconfiguration in your
  authentication middleware. Let me explain what's happening and
  walk you through the solution step by step...

With Espresso:
  Bug in auth middleware. Token expiry check uses `<` not `<=`. Fix:
```

Same information. 70-85% fewer tokens with the full stack.

### Two axes, not one

Caveman compresses how Claude **talks**. Ponytail compresses how much Claude
**writes**. Verbose prose is cheap next to the real waste: an agent that builds
a 120-line cache class, adds a dependency, scaffolds "for later", then iterates
on its own bloat. Ponytail stops it at the first solution that works, before the
wrong code is ever written. Espresso installs both so the two axes stack.

---

## Install

### Claude Code (in the Claude Code prompt)

3 commands. Type them inside Claude Code, not in a regular terminal.

```
/plugin marketplace add mirkobozzetto/espresso
/plugin install espresso@espresso
/reload-plugins
```

Or from a regular terminal:

```bash
claude plugin marketplace add mirkobozzetto/espresso
claude plugin install espresso@espresso
```

Then restart Claude Code. First session auto-configures the full stack.

### Cursor / Windsurf / Copilot / Codex / Others

These agents don't have plugin hooks. One command in your project root:

```bash
curl -sL https://raw.githubusercontent.com/mirkobozzetto/espresso/main/AGENTS.md > AGENTS.md
```

Codex, Cursor, Windsurf, Copilot, Amp, and Devin read `AGENTS.md` natively.
You get the output rules (40-60% savings) but not the full stack auto-install.

---

## Exa MCP — Web Search for Your Agent

Espresso rules enforce Exa as the only web search tool. Exa is a free hosted MCP — **no API key required**.

| Agent | Setup |
|-------|-------|
| **Claude Code** | `claude mcp add --transport http exa https://mcp.exa.ai/mcp` |
| **Codex** | Add `exa` MCP in `.codex/config.toml` with URL `https://mcp.exa.ai/mcp` |
| **Cursor** | Add to `~/.cursor/mcp.json`: `{"mcpServers": {"exa": {"url": "https://mcp.exa.ai/mcp"}}}` |
| **VS Code** | Add to `.vscode/mcp.json`: `{"servers": {"exa": {"type": "http", "url": "https://mcp.exa.ai/mcp"}}}` |
| **Claude Desktop** | Settings → Connectors → search "Exa" → click + |

Free plan includes generous rate limits. For production use, add your API key:
- Get one at [exa.ai/dashboard](https://dashboard.exa.ai/api-keys)
- Add header: `"x-api-key": "YOUR_KEY"` to MCP config

Docs: [docs.exa.ai/docs/reference/exa-mcp](https://docs.exa.ai/docs/reference/exa-mcp)

---

## Optional Companions

Espresso auto-configures these **if already installed**. Install them for maximum savings:

```bash
npm install -g gitnexus                     # Code intelligence — knowledge graph for your codebase
brew install rtk-ai/tap/rtk                 # CLI output compression (60-90%)
```
```
/install-plugin JuliusBrussee/caveman       # Conversation compression (~75%)
```

Restart your agent after installing any of these. Espresso detects and configures on next session.

**Ponytail is the exception**: you don't install it yourself. Espresso installs
the real [ponytail](https://github.com/DietrichGebert/ponytail) plugin for you on
first run (it runs the same `marketplace add` + `install` commands you would).
It's the upstream plugin, not a copy, so it updates from its own marketplace
like any other plugin.

### What each companion does

**GitNexus** — builds a knowledge graph of your codebase (functions, classes, call chains, execution flows). Instead of Claude grepping through files to understand code, it queries the graph. Fewer file reads = fewer tokens. Espresso configures the MCP server and adds an auto-reindex hook that keeps the index fresh after every session.

**RTK** (Rust Token Killer) — transparent proxy that compresses CLI output before it enters context. `git status`, `npm test`, `docker ps` output shrinks 60-90%. You run commands normally — RTK intercepts and compresses automatically via hook.

**Caveman** — compresses Claude's conversation style. Drops articles, filler words, pleasantries, hedging. "Bug in auth middleware. Token expiry uses < not <=. Fix:" instead of 4 paragraphs. ~75% output token reduction.

**Ponytail** - the lazy senior dev. Before writing code, the agent climbs a
ladder: does this need to exist (YAGNI), stdlib, native platform feature,
installed dependency, one line, only then more. Stops at the first rung that
holds. Never cuts validation, security, or tests. The biggest token drain is an
agent over-building then iterating on its own bloat; ponytail kills it at the
source. Espresso installs the real plugin and pins it to ultra.

---

## What Gets Created

On first session (Claude Code / Codex), the install hook creates:

```
~/.claude/rules/
├── exa.md                         # Exa-only web search
├── git.md                         # Clean commits (no signatures)
├── gitnexus.md                    # GitNexus first for code exploration
└── project-rules-suggestion.md    # Suggest rules in new projects

~/.config/caveman/config.json      # {"defaultMode": "ultra"} (if Caveman found)
~/.config/ponytail/config.json     # {"defaultMode": "ultra"} (Ponytail companion)
~/.claude.json → mcpServers.gitnexus  # GitNexus MCP server (if binary found)
~/.claude/settings.json → hooks.Stop  # GitNexus auto-reindex (if binary found)
~/.claude/.espresso-active         # Mode flag
~/.claude/.espresso-setup-done     # First-run marker (prevents re-running)
~/.claude/.espresso-ponytail-done  # Ponytail install marker (install + update)
```

Nothing is created if it already exists.

---

## How It Works

Two hooks fire automatically:

1. **SessionStart** — first run: scans existing setup, installs only what's missing, outputs summary. Every run: injects output rules as system context.
2. **UserPromptSubmit** — reinforces rules every turn to prevent drift mid-session.

No skills, no extra files loaded in context. Pure hooks.

The ponytail companion has its own one-shot marker (`.espresso-ponytail-done`),
separate from the main setup flag. New users get it on install; existing users
get it on their next session after updating espresso. It runs once, then never
again.

### Cross-Agent Compatibility

| Agent | Method | Auto-install |
|-------|--------|-------------|
| **Claude Code** | Plugin hooks (SessionStart + UserPromptSubmit) | Yes — full stack |
| **Codex** | Plugin hooks (compatible via `CLAUDE_PLUGIN_ROOT`) | Yes — full stack |
| **Cursor** | `AGENTS.md` or `.cursor/rules/espresso.mdc` | No — rules only |
| **Windsurf** | `AGENTS.md` | No — rules only |
| **Copilot** | `AGENTS.md` | No — rules only |
| **Others** | `AGENTS.md` at project root | No — rules only |

Claude Code and Codex get the full stack (output rules + global rules + RTK hook + Caveman config + Ponytail plugin).
Other agents get the output rules via `AGENTS.md` — still 40-60% savings.

---

## Combined Savings

| Layer | Savings | Installed by Espresso |
|-------|---------|----------------------|
| Output rules | 40-60% | Always |
| Global rules | context savings | Always (Claude Code / Codex) |
| GitNexus | fewer file reads | If gitnexus binary found |
| RTK | 60-90% CLI | If RTK binary found |
| Caveman ultra | ~75% conversation | If Caveman plugin found |
| Ponytail | 47-77% on code tasks* | Always (real plugin auto-installed) |

**Full stack: 70-85% total token reduction** vs vanilla.

\*Ponytail's figure is measured on code-generation tasks, a different
denominator than the 70-85% prose number. They compress different things, so
don't add them together.

---

## Troubleshooting

### "Hook load failed: expected record, received undefined"

Cached old version. Full reset:

```
/plugin uninstall espresso@espresso
/plugin marketplace remove espresso
/plugin marketplace add mirkobozzetto/espresso
/plugin install espresso@espresso
/reload-plugins
```

### Update to latest version

```
/plugin marketplace update espresso
/reload-plugins
```

If still broken after update, do the full reset above.

### "1 error during load" after /reload-plugins

Run `/doctor` to see which plugin has the error.
If it says `espresso@espresso` — do the full reset.
If it says another plugin — espresso is fine, the error is elsewhere.

### Plugin installed but no effect

Restart Claude Code. Hooks only activate on session start.

---

## Uninstall

### Claude Code
```
/uninstall-plugin espresso
```

### Clean up everything Espresso created
```bash
rm ~/.claude/rules/exa.md ~/.claude/rules/git.md ~/.claude/rules/gitnexus.md ~/.claude/rules/project-rules-suggestion.md
rm ~/.claude/.espresso-active ~/.claude/.espresso-setup-done ~/.claude/.espresso-ponytail-done
rm ~/.config/caveman/config.json ~/.config/ponytail/config.json
```

The RTK hook in `~/.claude/settings.json` stays (it's useful independently).
Caveman plugin stays (uninstall separately with `/uninstall-plugin caveman` if wanted).
Ponytail plugin stays too (uninstall separately with `/uninstall-plugin ponytail` if wanted).

### Cursor / Windsurf / Others
Delete the `AGENTS.md` you copied, or remove `espresso.mdc` from `.cursor/rules/`.

---

<div align="center">

MIT License — [Mirko Bozzetto](https://github.com/mirkobozzetto)

</div>
