# Claude Code to Codex map

Translate older Claude tool names without duplicating platform branches in every skill.

| Claude Code | Codex |
|---|---|
| `Task` | `spawn_agent(task_name=..., message=...)` |
| Parallel tasks | Multiple independent agent calls when the current policy allows delegation |
| Follow-up or status | `followup_task`, `send_message`, `wait_agent`, `list_agents`, or `interrupt_agent` |
| `Skill` | Automatic description match, `/skills`, or `$skillname` |
| `TaskCreate`, `TaskUpdate`, `TaskList` | `update_plan` |
| `AskUserQuestion` | `request_user_input`; when the mode blocks it, `request_user_input_async`, then end the turn if the answer blocks the work, such as plan approval; chat only when neither is exposed |

Claude named agents are Markdown; Codex named agents are TOML. When no named Codex reviewer exists, pass the body of `agents/staff-reviewer.md`, the scope, and the evidence to a general worker as task instructions, not as a persona. For `staff-review`, set `fork_turns="none"` so the reviewer receives no parent conversation history, hand it the diff as an artifact, state in the task that it is read-only (a Codex custom agent inherits the parent turn's live sandbox and approval state, so its own file sets defaults, not isolation), then wait for its verdict.

Both clients discover `hooks/hooks.json` automatically. Commands resolve the plugin with `${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT}}`; Codex provides both variables for compatibility. Users must review and trust plugin hooks before Codex runs them.

Use `request_user_input` only when the current mode permits it.
Outside Plan mode, Codex permits it only when the user sets `default_mode_request_user_input = true` under `[features]` in `~/.codex/config.toml`.
Use `request_user_input_async` for missing information when available; continue independent work while its answer is pending.
A tool name in a skill does not make that tool available or change its permission rules.
