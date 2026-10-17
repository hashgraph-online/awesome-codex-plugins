---
name: agentpack-pack
description: Generate a local AgentPack context pack for Codex before editing.
license: AGPL-3.0-only
---

# AgentPack Pack

Use when the user invokes `$agentpack-pack <task>` or asks Codex to prepare full AgentPack context.

AgentPack prepares context. It does not prove correctness and does not replace code review or tests.

## Steps

1. Generate fresh context for the task:

```bash
agentpack pack --task "<task>"
```

2. Read `.agentpack/context.md`.
3. Inspect selected files before editing.
4. Use normal repo search if selected files miss obvious tests, config, routes, or callers.

If AgentPack MCP is available, prefer the pack or context MCP tool and use markdown as fallback.
