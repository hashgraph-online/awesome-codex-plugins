# Claude Code to Codex map

Translate older Claude tool names without duplicating platform branches in every skill.

| Claude Code | Codex |
|---|---|
| `Task` | `spawn_agent(task_name=..., message=...)` |
| Parallel tasks | Multiple independent agent calls when the current policy allows delegation |
| Follow-up or status | `followup_task`, `send_message`, `wait_agent`, `list_agents`, or `interrupt_agent` |
| `Skill` | Automatic description match, `/skills`, or `$skillname` |
| `TaskCreate`, `TaskUpdate`, `TaskList` | `update_plan` |
| `AskUserQuestion` | Use an available question tool within its mode and purpose limits; otherwise ask one concise chat question |

Claude named agents are Markdown; Codex named agents are TOML. When no named Codex reviewer exists, pass the body of `agents/staff-reviewer.md`, the scope, and the evidence to a general worker as task instructions, not as a persona. For `staff-review`, create a new context with no parent conversation, pass the diff as an artifact, state that the reviewer is read-only, then wait for its verdict.

Both clients discover `hooks/hooks.json` automatically. Commands resolve the plugin with `${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT}}`; Codex provides both variables for compatibility. Users must review and trust plugin hooks before Codex runs them.

Use interactive input tools only when the current mode permits them.
A tool name in a skill does not make that tool available or change its permission rules.
