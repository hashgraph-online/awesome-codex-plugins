---
name: agentpack-route
description: Run read-only AgentPack task routing for ranked files, tests, rules, commands, and warnings.
---

# AgentPack Route

Use when the user invokes `@agentpack-route <task>`.

This is read-only. Do not write `.agentpack/context.md` and do not edit source files from route output alone.

## Steps

1. Run:

```bash
agentpack route --task "<task>"
```

2. Return ranked files, likely tests, rules or skills, suggested commands, and warnings.
3. Tell Codex to verify selected files with actual code before editing.
4. If the task needs fuller context, suggest `@agentpack-pack <task>`.

If AgentPack MCP is available, prefer the equivalent route task tool.
