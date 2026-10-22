# Agent Deck

[![MCP](https://img.shields.io/badge/MCP-compatible-blue)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Keep the way you work consistent across coding agents and workspaces. Agent Deck gives every agent the right playbooks, tools, and credentials from one governed source of truth.

[![One playbook across coding agents — Agent Deck](https://img.youtube.com/vi/DVC70PgMY80/maxresdefault.jpg)](https://www.youtube.com/watch?v=DVC70PgMY80)

[Watch the 100-second overview](https://www.youtube.com/watch?v=DVC70PgMY80) — one playbook across agents and workspaces.

[Why](#why) · [Quick Start](#quick-start) · [How learning works](#how-learning-works) · [Delegate](#delegate-to-another-agent) · [Everyday commands](#everyday-commands) · [Docs](#documentation)

> **Bringing a friend (or starting cold)?** Follow the [one-page friend path](docs/FRIEND_PATH.md): cold machine → first deck switch → first Dealer issue.

## Why

You teach one coding agent how you work: how to open a PR, write a ticket, check a release, or use your knowledge base. Then you switch to another agent and teach it all again.

- **Consistency across agents.** The same playbook can guide Claude Code, Codex, Cursor, or another MCP client. You maintain one procedure instead of separate copies for every agent.
- **Consistency across workspaces.** Reusable PR rules, ticketing procedures, UI principles, and knowledge-base workflows live in one collection. Attach them to the decks that need them instead of duplicating them across repositories.
- **One governed source of truth.** A deck bundles the MCP services, credentials, and playbooks for one context. The agent sees only that deck. Switch decks instead of rewiring agents; improve a playbook once and reuse the lesson everywhere.

One MCP endpoint, registered once.

The execution half is [agent-dealer](docs/DIRECTION.md): queue tasks against a deck, approve the plan before anything runs, execute headless under budget caps, review results, and gate every outbound send — Dealer runs consume deck playbooks and file patch proposals back.

## Quick Start

> **macOS required.** API key secrets, OAuth client secrets, and OAuth tokens are stored in **macOS Keychain**. Linux and Windows are not supported for production use yet.

**Requirements:** Node.js 20+ · npm · Dashboard via `agent-deck start` / `agent-deck open` (listens on `127.0.0.1:1111`) · Agent Deck MCP `http://127.0.0.1:1110/mcp`

**1. Install and launch** (managed install — auto-updates, keeps existing `~/.agent-deck` data):

```bash
npx @agent-deck/cli@latest install
export PATH="$HOME/.local/bin:$PATH"
agent-deck start --daemon
```

**2. Register Agent Deck in your agent** (once per machine; `<client>` is `codex`, `cursor`, `claude`, or `muse`):

```bash
agent-deck setup --client <client>
```

Per-client details, restart and verify steps, and what `setup` installs: [Agent harness](docs/AGENT_HARNESS.md).

**3. Create a deck** in the dashboard (**My Decks** → create a deck → drag cards from **My Collection**), or ask the agent in chat to create one.

**4. Register playbooks (agent-first).** Describe the procedure in chat — e.g. *“Add a release checklist playbook with trigger ‘ship to npm’.”* Let the agent register it and attach it to your deck.

**5. Add external MCP servers and API keys** (Linear, Notion, Slack, …) in the dashboard — OAuth in the browser, API keys pasted once into Keychain — then drag the cards onto your deck.

**6. Pick a deck each session.** Tell the agent which deck — *“use the dev deck”*, or mid-session *“switch to my personal deck”* — and approve the switch as This session only or This workspace by default. Or run `agent-deck use <deck>` in a repo so the deck binds on session open without naming it.

Same decks on another machine: keep `~/.agent-deck/` in a private Git repository you own, push and pull it yourself, then run `agent-deck reindex` — see [Store format](docs/STORE_FORMAT.md).

## How learning works

When you correct a playbook-driven result, Agent Deck turns the lesson into a reviewable patch proposal so future sessions start from what you taught it. Corrections become **proposals** you review in the dashboard (Playbook patches); accepted changes update the deck. Every run makes the next one better.

If you use per-repo `use` stubs and playbook triggers changed, refresh with `agent-deck use --refresh`.

## Delegate to another agent

To delegate a task to a local agent session on a deck, `agent-deck run` launches a signed-in client bound to that deck:

```bash
agent-deck run mydeck --client claude --cwd /path/to/repo --prompt-file ./brief.md --tools readonly
```

Per-client flags, resume, and trust behavior: [DELEGATION.md](docs/DELEGATION.md).

## Install as an agent plugin

The repo root is one plugin: one `skills/` folder (`agent-deck-session`, `agent-deck-playbooks`, `agent-deck-setup`, `agent-deck-run`) plus `.mcp.json`, described by a manifest per client. Prerequisites for delegation: agent-deck >= 2.1.0 and the daemon running (see Quick Start), and the client CLI you delegate to, installed and signed in. The `agent-deck-setup` skill checks these and tells you what is missing.

| Client | Install | Manifest |
| --- | --- | --- |
| Claude Code | `/plugin marketplace add not-so-fat/agent-deck`, then `/plugin install agent-deck@agent-deck` | `.claude-plugin/plugin.json` + `marketplace.json` |
| Cursor | add `not-so-fat/agent-deck` as a plugin marketplace and install **agent-deck** | `.cursor-plugin/plugin.json` + `marketplace.json` |
| Codex | `codex plugin marketplace add not-so-fat/agent-deck`, then `codex plugin add agent-deck@agent-deck` | `.codex-plugin/plugin.json` (Codex reads the marketplace from `.claude-plugin/marketplace.json`) |
| muse | `agent-deck setup --client muse` (installs the four skills into `~/.config/muse/skills/`), or `muse plugins install <clone path>` (muse imports `.claude-plugin/plugin.json`) | `.claude-plugin/plugin.json` |

Skills are never copied by hand: the muse copies come from root `skills/` via `scripts/copy-muse-skills.mjs` at build time and `agent-deck setup --client muse` at install time.

### Cursor: setup and a test task

1. Install agent-deck and start it (Quick Start above): `npx @agent-deck/cli@latest install`, `agent-deck start --daemon`, then `agent-deck doctor`.
2. Install the **agent-deck** plugin from the Cursor Marketplace (or, for local testing, copy this repo to `~/.cursor/plugins/local/agent-deck` and run **Developer: Reload Window**). The plugin adds the four skills and the `agent-deck` MCP server (`agent-deck mcp-launch`, from `.mcp.json`); it needs the `agent-deck` CLI on `PATH` and stores no secrets.
3. Create a deck in the dashboard (`agent-deck open`), then bind a project folder: `agent-deck use <deck> --client cursor`, and reload Cursor.
4. **Test task:** open that folder and ask the agent: *"Use the agent-deck-setup skill to check my Agent Deck setup and tell me what is missing."* Expected: it runs read-only checks (`agent-deck --version`, `agent-deck status`, `agent-deck deck list`) and reports the result. Then try delegation: *"Use agent-deck-run to have a read-only claude session on deck <deck> list the files in this folder, and report its answer."* Expected: it launches `agent-deck run <deck> --client claude --tools readonly --detach`, polls `agent-deck run status`, and reports the session's answer with the `runId` and `sessionId`.

## Everyday commands

```bash
agent-deck start --daemon
agent-deck open             # re-open dashboard with a fresh auth cookie
agent-deck use <deck>       # bind this folder to a deck
agent-deck export all -o backup.agent-deck.json
agent-deck credential list
agent-deck exec --connections cred_id -- <command>
agent-deck upgrade
agent-deck stop
```

Port conflicts: `agent-deck status` · `agent-deck start --force`. Full environment reference: [Setup](docs/SETUP.md).

## Documentation

**Index:** [docs/README.md](docs/README.md) · **Security:** [SECURITY.md](SECURITY.md)

| Guide | Description |
|-------|-------------|
| [Friend path](docs/FRIEND_PATH.md) | Cold machine → first deck switch → first Dealer issue |
| [Direction](docs/DIRECTION.md) | Cross-product direction — agent_deck + agent-dealer |
| [Setup](docs/SETUP.md) | Ports, env vars, secrets, troubleshooting |
| [MVP](docs/MVP.md) | Source of truth — decks, vault, playbooks, MCP tools |
| [Agent harness](docs/AGENT_HARNESS.md) | What `setup` installs |
| [Delegation](docs/DELEGATION.md) | `agent-deck run` per-client reference |
| [Agent run API](docs/AGENT_RUN_API.md) | Same-host HTTP start, observe, cancel, and resume |
| [Playbooks vs Cursor skills](docs/PLAYBOOKS_AND_SKILLS.md) | Deck playbooks vs Cursor skills |
| [Export / import](docs/PRD_EXPORT_IMPORT.md) | Portable layout bundles |
| [Store format](docs/STORE_FORMAT.md) | File-backed store layout, sync, reindex |
| [Deck display](docs/PRD_DECK_DISPLAY.md) | Terminal status line |
| [Codex / Claude plugin](docs/CODEX_PLUGIN.md) | Marketplace packaging (HOL / Codex / Claude Code) |
| [Architecture](docs/ARCHITECTURE.md) | SQLite, Keychain, components |
| [Development](docs/DEVELOPMENT.md) | Contributors |
| [Publishing](docs/PUBLISHING.md) | npm release |

## License

MIT — see [LICENSE](LICENSE).
