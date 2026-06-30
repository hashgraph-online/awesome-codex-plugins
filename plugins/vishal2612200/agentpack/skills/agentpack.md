---
name: agentpack
description: Explain AgentPack status and choose the next local context step in a Codex session.
---

# AgentPack

Use when the user invokes `@agentpack` or asks whether AgentPack context is ready.

AgentPack is not a coding agent. AgentPack is a local context engine that helps Codex start with ranked repo context.

## Steps

1. Check whether `.agentpack/context.md` exists.
2. If it exists, inspect its freshness block and task summary before editing.
3. If context is missing or stale, suggest `@agentpack-route <task>` for read-only orientation or `@agentpack-pack <task>` for a context pack.
4. Tell Codex to treat selected files as a starting map, not proof of correctness.
5. Use normal repo search when AgentPack output looks incomplete.

## Local commands

```bash
agentpack status
agentpack route --task "<task>"
agentpack pack --task "<task>"
```

Prefer AgentPack MCP tools when available: route first, then fetch full context only when needed.
