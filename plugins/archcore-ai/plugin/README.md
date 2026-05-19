# Archcore Plugin

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Make your AI code like it already knows your repo.**

Archcore gives coding agents the architecture, rules, and prior decisions of *this* repo — so new changes land where your project says they belong and follow the team's conventions, automatically.

Works in **Claude Code**, **Cursor**, and **Codex CLI**. One source of truth, in Git.

## Commands

Describe what you want in plain English — Archcore routes it. The slash commands below are shortcuts to the same workflows.

| Command              | Outcome                                                | When to use                                                                                                                       |
| -------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `/archcore:init`     | Make your repo legible to AI agents                    | First-time setup — seeds a stack rule, a run-the-app guide, and imports your `CLAUDE.md` / `AGENTS.md` / `.cursorrules` if present |
| `/archcore:context`  | Load what's already decided before you change code     | Daily, before editing — pulls relevant rules, decisions, specs, and patterns for a file, directory, or topic                      |
| `/archcore:capture`  | Document what already lives in code                    | A module, API, pipeline, or integration has tribal knowledge but no doc yet                                                       |
| `/archcore:plan`     | Turn an idea into a scoped implementation plan         | New feature, refactor, or initiative — pick depth with `--track product\|feature\|sources\|iso`                                   |
| `/archcore:decide`   | Record a decision and (optionally) make it a team rule | A decision was made — capture rationale, consequences, and turn it into an enforced standard                                      |
| `/archcore:audit`    | Find stale, missing, or drifting docs                  | Health check — add `--deep` for a full audit, `--drift` for code/doc staleness                                                    |
| `/archcore:help`     | Navigate the skill catalog                             | When you forget which command fits                                                                                                |

## Install

Archcore plugins require the **Archcore CLI** on `PATH` — it serves the MCP server the plugin talks to.

```bash
# macOS / Linux / WSL
curl -fsSL https://archcore.ai/install.sh | bash

# Windows (PowerShell 5.1+)
irm https://archcore.ai/install.ps1 | iex
```

Verify: `archcore --version` · Update: `archcore update` · Docs: [docs.archcore.ai/cli/install](https://docs.archcore.ai/cli/install/)

Then add the plugin in your host:

**Claude Code**

```bash
/plugin marketplace add archcore-ai/plugin
/plugin install archcore@archcore-plugins
```

**Cursor** — requires Cursor 2.5+. Open **Plugins**, paste `https://github.com/archcore-ai/plugin` into **Search or paste link**, click **Add Plugin**. One-time MCP setup: copy [`docs/cursor.mcp.example.json`](docs/cursor.mcp.example.json) into `~/.cursor/mcp.json` (user-scoped) or `.cursor/mcp.json` (project-scoped).

**Codex CLI** — requires Codex CLI v0.117.0+.

```bash
codex plugin marketplace add archcore-ai/plugin
codex
# then run /plugins, open Archcore, select Install plugin
```

<details>
<summary>Local development & team rollouts</summary>

**Claude Code** — load the plugin for the current session:

```bash
claude --plugin-dir /path/to/plugin
```

**Cursor** — symlink the repo into Cursor's local plugins directory and reload the window:

```bash
ln -s /path/to/plugin ~/.cursor/plugins/local/archcore
# then in Cursor: Cmd/Ctrl+Shift+P → "Developer: Reload Window"
```

**Cursor team rollouts** — Dashboard → Settings → Plugins → Team Marketplaces → Import (paste the GitHub URL).

</details>

## Try these first

Open your project and try these three prompts. Each shows a different side of what your agent can now do.

> Empty repo? Run `/archcore:init` first — it seeds a stack rule, a run-the-app guide, and optionally imports your existing `CLAUDE.md` / `AGENTS.md` / `.cursorrules`.

**1. "Before I change anything in `src/auth/`, what should I know?"**
Your agent sees what's already decided for that path — *before* it touches the code.

**2. "Add a new API handler and follow this repo's conventions."**
Your agent places the handler where your architecture says it belongs, instead of guessing.

**3. "We picked PostgreSQL — record it as a team standard."**
The decision is captured, codified as a rule, and auto-applied to every future change in the same area. Decisions stop dying in chat scrollback.

## What changes after install

Without Archcore, the agent guesses your folder structure, re-litigates decisions your team already made, needs the same conventions repeated in every chat, and loses project truth the moment the session ends.

With Archcore, the same asks produce code that lands where your architecture says it belongs, respects decisions already in Git, follows team conventions loaded automatically, and reflects new decisions as future guardrails — not markdown graveyards.

## Use Archcore when

- Your agent writes code, but not the way this repo expects
- Your `CLAUDE.md` / `.cursorrules` / `AGENTS.md` keeps growing and drifting
- You work with 2+ agents or 2+ host tools (Claude Code + Cursor + Codex)
- You want decisions, rules, and specs in Git — not in chat scrollback

**Not for** — chat memory, a prompt library, or a one-shot spec-to-code generator. Archcore is a repo truth layer for coding agents, not a methodology kit.

## Supported hosts

| Host            | Status      | Install            |
| --------------- | ----------- | ------------------ |
| **Claude Code** | Production  | Plugin marketplace |
| **Cursor**      | Implemented | Plugin marketplace |
| **Codex CLI**   | Implemented | Plugin marketplace |
| GitHub Copilot  | Planned     | —                  |

Built on open standards (Agent Skills, MCP) — skills and MCP tools are shared across hosts; only manifests are host-specific.

## How Archcore differs

| Tool                       | Category    | How Archcore differs                                                                            |
| -------------------------- | ----------- | ----------------------------------------------------------------------------------------------- |
| **BMAD / Spec Kit / Agent OS** | Methodology | Archcore stores *artifacts* and a living context graph; methodology kits prescribe *process*.   |
| **Superpowers**            | Methodology | Shapes *agent behavior*; Archcore provides *canonical project knowledge* any agent can read.    |
| **claude-mem / Mem0 / agentmemory** | Memory      | They remember *what you did*; Archcore stores *how the system is built and what was decided*.   |
| **Cline Memory Bank**      | Docs        | Same spirit, lower ceremony. Archcore adds typed relations and validated multi-step cascades.   |

Pick a methodology tool for an opinionated dev flow. Pick a memory tool for session continuity. Pick Archcore when you want typed, queryable **project truth** that your coding agent respects on every request.

## Uninstall

**Claude Code:** `/plugin uninstall archcore@archcore-plugins`
**Cursor:** remove from plugin settings.
**Codex CLI:** `codex plugin uninstall archcore`

## License & contributing

[Apache-2.0](LICENSE) · Issues and ideas: [GitHub Issues](https://github.com/archcore-ai/plugin/issues)
