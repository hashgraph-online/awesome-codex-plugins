# Claude Code adaptation

The Kuudo plugin's `SessionStart` hook injects the complete `kuudo-skills:using-kuudo` skill on `startup`, `clear`, and `compact`. Treat this bootstrap as already loaded; do not invoke it again.

For a selected leaf skill:

1. Announce it in the format required by the bootstrap.
2. Invoke `kuudo-skills:<skill-name>` with Claude Code's Skill tool.
3. Follow the current skill body.

Use only the tools, resources, prompts, names, and schemas exposed in the current session. The client owns MCP configuration and authentication. A missing MCP capability can limit execution, but it does not change which skill applies.
