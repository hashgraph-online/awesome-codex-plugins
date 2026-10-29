---
name: steinwall
description: SteinWall cost, savings and safety information, and a security check for extensions. Use when the user asks what the coding agent costs today or this month, how much budget is left, what was blocked or saved, or before installing a skill, plugin or MCP server ("is this safe to install?", "check this skill").
---

# SteinWall

SteinWall runs locally next to the coding agent (Claude Code or Codex). Its command-line tool is available at `~/.steinwall/bin/steinwall.mjs`. Run it with Node from any shell:

- `node ~/.steinwall/bin/steinwall.mjs status`: cost today and this month, budgets, blocked actions, loop rescues.
- `node ~/.steinwall/bin/steinwall.mjs report`: daily report with estimated savings. Add `--date YYYY-MM-DD` for an earlier day.
- `node ~/.steinwall/bin/steinwall.mjs scan <path>`: check a skill, plugin or MCP config before installing it. Exit code 2 means do not install.
- `node ~/.steinwall/bin/steinwall.mjs scan --installed`: check everything that is already installed.

On Windows PowerShell, use `node "$HOME/.steinwall/bin/steinwall.mjs" status`.

Show the output to the user. Amounts are estimates at API list prices and are marked with "≈".

## What is reserved for the user

Changing the budget, lifting a budget stop, editing the configuration and installing the status line are reserved for the user. SteinWall refuses these commands when an agent runs them. If one is needed, tell the user the command, for example `/steinwall:budget --daily 40` in Claude Code, or `steinwall budget override` in a terminal.

When SteinWall blocks an action, it explains why in the tool result. Do not retry the action in a modified form. Explain the block to the user and let them decide.
