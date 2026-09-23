---
name: agent-deck-setup
description: Use when setting up Agent Deck, the MCP is disconnected, or the local daemon is down. Guides install/start with read-only checks; the user runs install commands.
---

# Agent Deck setup

Treat setup as three separate layers: daemon health, host transport, then folder assignment.

1. Run `agent-deck status` and check `http://127.0.0.1:1110/health` (or `<mcp-url>/health`
   from `.agent-deck/use.json` if present).
2. If the daemon is down, tell the user to run:
   - `npm i -g agent-deck`
   - `agent-deck start --daemon`
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
5. Once transport and assignment are valid, use the session skill and require
   `get_session_binding` followed by `get_bound_deck`.
6. Do not invent credentials, ports, or shell install pipelines. Keep guidance read-only;
   the user executes install and setup commands.
