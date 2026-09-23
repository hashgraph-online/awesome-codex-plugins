---
name: agent-deck-session
description: Use at session start when Agent Deck MCP is configured or expected, including launch-selected sessions, or when the user asks for the deck status line / which deck is active.
---

# Agent Deck session opener

This skill verifies an MCP connection; it does not create one. In Codex, the Agent Deck
plugin's `.mcp.json` must already have launched `agent-deck mcp-launch`. The launcher reads
the folder's v3 assignment and sends the deck/workspace headers before these tools exist.

When Agent Deck MCP is configured for the current session, or `.agent-deck/use.json` indicates
that it is expected, this opener is a hard gate. The file is only one optional signal; the
gate also includes launch-selected sessions that deliberately have no assignment file.
Complete the opener before reading repository files, running task commands, or answering the
task. Once per conversation (or after the selected deck changes):

1. `get_session_context` — one call returns the workspace, effective deck,
   `display_summary`, services, credential metadata, and playbook summaries
2. Print **exactly one** line from `display_summary` (e.g. `◆ dev · 2 MCP · 0 keys · 1 playbooks`)
3. Match the task against the returned playbook triggers. For every match, use the
   `agent-deck-playbooks` skill and call `get_playbook` before taking task action.

If the Agent Deck tools are unavailable, disconnected, return `GRANT_REQUIRED`, or the
required call fails, stop and report the connection problem. Do not inspect the repository,
improvise from memory, or silently fall back to another route. Before the gate passes,
checking for the optional assignment signal, checking whether Agent Deck is configured, and
other read-only diagnostics needed to restore the connection are allowed.

Give the operator recovery for the failed layer:

- **Transport unavailable:** run `agent-deck status`. In Codex, verify the Agent Deck plugin
  is installed, enabled, and current, then reload or start a new task so its `.mcp.json`
  launches `agent-deck mcp-launch`. `agent-deck setup --client codex` installs or refreshes
  the AGENTS.md guidance only; it does not install or repair the plugin transport.
- **Assignment missing or legacy:** run `agent-deck use <deck>` in the IDE folder, then reload
  or retry the MCP connection.
- **Unattended launch:** fix `x-agent-deck-deck-id` / the launch configuration.

Do not repeat the status line every turn unless the user asks or the bind changes.
