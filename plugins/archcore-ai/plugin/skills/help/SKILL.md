---
name: help
description: "Show available Archcore commands and how to use them. Use when onboarding, exploring what skills are available, or when you're not sure which command to run."
---

# /archcore:help

Guide to what you can do with the Archcore plugin.

## When to use

- "What can I do with Archcore?"
- "Help"
- "What commands are available?"

## Routing table

No routing needed. Single behavior: present the command guide.

## Execution

Present the following guide:

---

## Commands

Describe what you need — the agent picks the right skill. Slash commands are shortcuts.

| Command | What it does |
|---|---|
| `/archcore:init` | First-time setup — seed stack rule, run guide, optional imports from CLAUDE.md / AGENTS.md / .cursorrules |
| `/archcore:context [path, topic, --git-changes]` | Surface rules, ADRs, specs, and patterns that apply to a code area (or your `--git-changes`), or pick up where work left off |
| `/archcore:capture [topic]` | Document a module, component, or topic (picks ADR / spec / doc / guide automatically) |
| `/archcore:decide [topic]` | Record a finalized decision (ADR, optionally codified as rule + guide or formalized as spec + plan) or open proposal (RFC) |
| `/archcore:plan [feature]` | Plan a feature end-to-end. Default flow: idea → PRD → plan. Switch with `--track product\|feature\|sources\|iso` |
| `/archcore:audit` | Documentation dashboard. `--deep` for full audit, `--drift` for code/cascade/temporal staleness |
| `/archcore:help` | Show this guide |

**Tip:** You can also just describe what you need in natural language. The agent will pick the right command automatically.

## Plan tracks (`--track`)

| Track | Flow | Use when |
|---|---|---|
| `product` *(default)* | idea → PRD → plan | Lightweight individual feature or rapid prototyping |
| `feature` | PRD → spec → plan → task-type | Well-scoped feature with formal contract + repeatable pattern |
| `sources` | MRD → BRD → URD | Discovery research: market, business, user inputs |
| `iso` | BRS → StRS → SyRS → SRS | Formal ISO 29148 cascade for regulated systems |

Invoke: `/archcore:plan "<topic>" --track <name>`.

## Decide continuations

After `/archcore:decide` creates an ADR, it can extend the chain:

- **Standard cascade** (rule + guide) when the decision is enforceable.
- **Architecture cascade** (spec + plan) when the decision needs a formal technical contract.

You can also explicitly request: *"and make it a standard"* or *"and formalize the contract"*.

## Direct document creation

There are no per-type slash commands. Create documents through the commands above, or call `mcp__archcore__create_document` directly when you need exact type-level control:

- Market / business / user requirements (`mrd` / `brd` / `urd`) → `/archcore:plan --track sources`
- ISO 29148 cascade (`brs` → `strs` → `syrs` → `srs`) → `/archcore:plan --track iso`
- Any type directly → `mcp__archcore__create_document(type=<slug>)`

## Setup

If Archcore commands fail with MCP tool errors, the CLI needs to be installed:

1. **Install CLI:** `curl -fsSL https://archcore.ai/install.sh | bash`
2. **Initialize project:** `archcore init`
3. **Restart** the session

The plugin provides skills, agents, and hooks — but document operations (create, update, delete) require the Archcore CLI, which runs the MCP server.

---

## Result

The guide above, presented as-is. No additional commentary needed.
