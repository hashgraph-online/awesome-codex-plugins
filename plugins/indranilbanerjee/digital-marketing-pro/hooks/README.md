# Hooks: one live-write gate, no lifecycle hooks

`hooks.json` registers one hook since 3.42.0 (below) and nothing else. This file carries the rationale that used to live in a `_readme` field inside `hooks.json` itself — moved here because Cowork's plugin validation rejects unknown top-level fields in `hooks.json` ([issue #9](https://github.com/indranilbanerjee/digital-marketing-pro/issues/9)).

Digital Marketing Pro ships NO lifecycle hooks as of v3.1.0. Earlier versions registered SessionStart, PreToolUse Write/Edit, PreToolUse mcp_.*, and SessionEnd hooks that fired on EVERY Claude Code operation in EVERY project — not just DMP work — because Claude Code plugin hooks have no per-directory or per-project scoping. The PreToolUse mcp_.* matcher was particularly problematic: it intercepted EVERY MCP tool call from ANY plugin, gating all MCP writes through DMP's brand-compliance prompt regardless of context. Their work (dependency check, brand compliance, MCP write-operation guard, session-end insight saving) already lives at the right architectural layer: per-agent compliance instructions, manual `python3 scripts/setup.py` invocation when needed, and per-agent decision flows for MCP writes that already require explicit user approval. Prior config preserved at hooks/hooks-reference.example.json with rationale notes per hook. To re-enable a specific hook, copy its entry into the 'hooks' object below.

## The one hook: `gate_live_writes.py` (3.42.0)

A live write is three shell commands the model runs itself: `connector_executor.py --execute` (prepare),
`approval-manager.py --action approve` (or `create-standing`), then `connector_executor.py --execute --approval-id`
(fire). The approval record proves those steps ran in order; only the host's permission prompt shows them to a
person. A saved allow rule ("Yes, and don't ask again" on the executor's path) or a skill's `allowed-tools` would
skip that prompt, so this PreToolUse hook answers `"ask"` for those commands and Claude Code prompts anyway.

- **When it runs:** only for Bash or PowerShell commands that name `approval-manager` or `connector_executor`
  (the `if` filters in `hooks.json`). Every other command, in every project, starts no process.
- **What it does:** a string check on the command (no model call, no network, no file access); output is a
  `permissionDecision: "ask"` with a reason, or nothing.
- **Limits:** it reads the command text, so a command that reaches the scripts without naming them (a glob, a
  wrapper script) is not seen; bypass-permissions mode can skip prompts; hosts other than Claude Code may not run
  plugin hooks. The typed `yes` in each skill stays in place for those cases.
- **Tests:** `tests/test_live_write_gate.py`.
