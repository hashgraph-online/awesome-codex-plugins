# Codex adaptation

The Kuudo Codex plugin exposes `./skills/` through native skill discovery and intentionally supplies no session hook. For relevant Amazon commerce work, load `using-kuudo` before the selected leaf skill.

Inspect the current `SKILL.md` body before acting. If Codex reports that skill descriptions were shortened to fit the skills context budget, every skill remains discoverable, but its full instructions still need to be read.

Use only the tools, resources, prompts, names, and schemas exposed in the current session. The client owns MCP configuration and authentication. A missing MCP capability can limit execution, but it does not change which skill applies.
