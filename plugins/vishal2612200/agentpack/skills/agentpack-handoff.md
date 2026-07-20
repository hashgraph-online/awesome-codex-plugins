---
name: agentpack-handoff
description: Package current work for another real agent session.
---

# AgentPack Handoff

Use when the user invokes `$agentpack-handoff [name]` in Codex or `/agentpack-handoff [name]` in Claude Code.

Inspect the current task, acceptance criteria, work completed and remaining, decisions, blockers, next action, Git-visible changes, and real validation evidence. Create the mandatory structured report, then call MCP `create_handoff(report=..., name="<requested name>")`. If MCP is unavailable, run `agentpack handoff create --input <report.json> --name "<requested name>"`.

Use `not_run` plus a reason for validation that did not run. Do not claim checks passed without evidence. Return the generated memorable name, never the internal handoff UUID.
