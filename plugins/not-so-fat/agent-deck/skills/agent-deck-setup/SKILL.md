---
name: agent-deck-setup
description: Use when setting up Agent Deck, the MCP is disconnected, or the local daemon is down. Guides install/start with read-only checks; the user runs install commands.
---

# Agent Deck setup

Treat setup as three separate layers: daemon health, host transport, then folder assignment.

1. Run `agent-deck status` and check `http://127.0.0.1:1110/health` (or `<mcp-url>/health`
   from `.agent-deck/use.json` if present).
2. If agent-deck is missing, older than 2.1.0 (`agent-deck --version`), or the daemon is down, tell the user to run the matching fix:
   - Not installed (macOS, Node.js 20+, npm): `npx @agent-deck/cli@latest install`, then `export PATH="$HOME/.local/bin:$PATH"` (managed install: launcher in `~/.local/bin`, versions under `~/.agent-deck/`).
   - Outdated: `agent-deck upgrade` (`agent-deck upgrade --check` reports whether one is available).
   - Daemon down: `agent-deck start --daemon`.
   - `agent-deck doctor` prints any harness repair as `agent-deck setup --client <client>`; run it, then restart that host.
3. If the daemon is healthy but MCP tools are unavailable, repair the host transport:
   - **Codex:** verify the Agent Deck plugin is installed, enabled, and current. Its bundled
     `.mcp.json` must run `agent-deck mcp-launch`; reload or start a new task after changing
     the plugin. Run `agent-deck setup --client codex` to merge the Agent Deck bootstrap
     guidance into `~/.codex/AGENTS.md` (or add `--scope project` for `./AGENTS.md`). This
     command preserves content outside Agent Deck's markers and does not install the plugin.
   - **Cursor / Claude:** run `agent-deck setup --client cursor|claude --start`, then restart
     that host.
4. Check the folder assignment reported by `agent-deck status`. If it is missing or legacy,
   tell the user to run `agent-deck use <deck>` in that folder, then reload or retry MCP.
5. For delegation (`agent-deck run`), the client CLI must also be installed and signed in. Check `claude auth status`, `codex login status`, `cursor-agent status`, or `muse --version`; if missing, point the user to the official install docs ([Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup), [Codex](https://developers.openai.com/codex/cli), [Cursor CLI](https://cursor.com/docs/cli/installation); muse per its distribution) and its sign-in (`claude`, `codex login`, `cursor-agent login`, `muse login`).
6. If no deck exists (`agent-deck deck list`), the user creates one in the dashboard (`agent-deck open` → My Decks) or imports one: `agent-deck import <file>.agent-deck.json`.
7. Once transport and assignment are valid, use the session skill and require
   `get_session_binding` followed by `get_bound_deck`.
8. Do not invent credentials, ports, or shell install pipelines. Keep guidance read-only;
   the user executes install and setup commands.
