---
name: agentpack-resume
description: Claim and resume a handoff from another real agent session.
---

# AgentPack Resume

Use when the user invokes `@agentpack-resume [name]` in Codex or `/agentpack-resume [name]` in Claude Code.

Call MCP `accept_handoff(name="<name>")` when available. If MCP is unavailable, run `agentpack handoff resume <name>`. A missing name is valid when only one pending handoff exists. Use the report and bounded fresh context returned by AgentPack, then continue from `next_action`. Never reconstruct or apply the patch manually.
