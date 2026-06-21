---
name: agentpack-pack
description: Generate a local AgentPack context pack for Codex before editing.
---

# AgentPack Pack

Use when the user invokes `@agentpack-pack <task>` or asks Codex to prepare full AgentPack context.

AgentPack prepares context. It does not prove correctness and does not replace code review or tests.

## Steps

1. Write the task:

```bash
agentpack task set "<task>"
```

2. Generate fresh context:

```bash
agentpack pack --task auto
```

3. Read `.agentpack/context.md`.
4. Inspect selected files before editing.
5. Use normal repo search if selected files miss obvious tests, config, routes, or callers.

If AgentPack MCP is available, prefer the pack or context MCP tool and use markdown as fallback.
