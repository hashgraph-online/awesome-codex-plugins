---
name: agentpack
description: Route normal development through AgentPack's work, learn, finish, and doctor loop.
license: AGPL-3.0-only
---

# AgentPack

Use when the user invokes `$agentpack`, asks what to do next, or wants the normal AgentPack product workflow.

AgentPack is not a coding agent. AgentPack is a local context engine that helps Codex start with ranked repo context.

## Product Loop

1. Start concrete work with `agentpack work "<task>"`.
2. During or after work, use `agentpack learn --json` to present the next three evidence-backed topics.
3. Finish with `agentpack finish` so checks and task memory are recorded.
4. Use `agentpack doctor` when integration or context health is unclear.

Use `$agentpack-review`, `$agentpack-resolve`, `$agentpack-pack`, `$agentpack-route`, and `$agentpack-handoff` for those specialized workflows. Treat selected files as a starting map, not proof of correctness, and use normal repository search when AgentPack context is incomplete.

## Local commands

```bash
agentpack status
agentpack work "<task>"
agentpack learn --json
agentpack finish
agentpack doctor
```

Prefer AgentPack MCP tools when available: route first, then fetch full context only when needed.
