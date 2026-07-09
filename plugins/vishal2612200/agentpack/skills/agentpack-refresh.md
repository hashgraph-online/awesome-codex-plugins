---
name: agentpack-refresh
description: Refresh AgentPack context when task, git state, or repo files changed.
---

# AgentPack Refresh

Use when the user invokes `@agentpack-refresh`, context looks stale, or task/git state changed.

## Steps

1. Run the portable refresh path:

```bash
agentpack pack --agent codex --task auto
```

2. If the task changed, update it first:

```bash
agentpack task set "<task>"
agentpack pack --agent codex --task auto
```

3. Read `.agentpack/context.md` after refresh.
4. Warn if context still appears stale or task text does not match.
5. Treat the pack as a map, not proof of correctness.

Prefer AgentPack MCP refresh/get-context behavior when available.
