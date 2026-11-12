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
   - **Codex:** verify the Agent Deck plugin is installed, enabled, and current. Codex connects
     over pure MCP (streamable HTTP): a global headerless fallback plus a per-folder entry
     carrying the workspace header — no `agent-deck` executable lookup. Trust the folder,
     approve the project agent-deck entry, run `agent-deck use <deck>` in the folder when its
     assignment is missing or legacy, then reload or start a new task. Run `agent-deck setup
     --client codex` to write the global fallback and merge the Agent Deck bootstrap
     guidance into `~/.codex/AGENTS.md` (or add `--scope project` for `./AGENTS.md`). This
     command preserves content outside Agent Deck's markers and does not install the plugin.
   - **Claude Code:** same pure-MCP connection as Codex (global fallback in `~/.claude.json`
     plus project `.mcp.json` with the workspace header). Trust the folder, approve the
     project entry, run `agent-deck use <deck>` when the assignment is missing or legacy,
     then reload MCP. `agent-deck setup --client claude` writes the fallback.
   - **Cursor:** same pure-MCP connection as Codex (global fallback in
     `~/.cursor/mcp.json` plus project `.cursor/mcp.json` with the workspace
     header — no `agent-deck` executable lookup). `agent-deck setup --client
     cursor` writes the fallback; approve the project server, run `agent-deck
     use <deck>` when the assignment is missing or legacy, then reload MCP.
   - **Muse:** same pure-MCP connection (global headerless fallback in the
     user settings — no `agent-deck` executable lookup). `agent-deck setup
     --client muse` writes the fallback and installs the native bootstrap
     skills; run `agent-deck use <deck>` in the folder when its assignment is
     missing or legacy, trust the folder, then reload MCP (restart Muse).
     Verify with `/mcp` — unassigned folders land in the explain-only session.
4. Check the folder assignment reported by `agent-deck status`. If it is missing or legacy,
   tell the user to run `agent-deck use <deck>` in that folder, then reload or retry MCP.
5. For delegation (agents use the MCP `start_run` tool; the run executes on this host), the client CLI must also be installed and signed in on the host. Check `claude auth status`, `codex login status`, `cursor-agent status`, or `muse --version`; if missing, point the user to the official install docs ([Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup), [Codex](https://developers.openai.com/codex/cli), [Cursor CLI](https://cursor.com/docs/cli/installation); muse per its distribution) and its sign-in (`claude`, `codex login`, `cursor-agent login`, `muse login`).
6. If no deck exists (`agent-deck deck list`), the user creates one in the dashboard (`agent-deck open` → My Decks) or imports one: `agent-deck import <file>.agent-deck.json`.
7. Once transport and assignment are valid, use the session skill and require
   `get_session_binding` followed by `get_bound_deck`.
8. Do not invent credentials, ports, or shell install pipelines. Keep guidance read-only;
   the user executes install and setup commands.
