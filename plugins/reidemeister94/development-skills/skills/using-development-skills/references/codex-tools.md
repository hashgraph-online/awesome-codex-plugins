# Claude Code to Codex map

Translate older Claude tool names without duplicating platform branches in every skill.

| Claude Code | Codex |
|---|---|
| `Task` | `spawn_agent(task_name=..., message=...)` |
| Parallel tasks | Multiple independent agent calls when the current policy allows delegation |
| Follow-up or status | `followup_task`, `send_message`, `wait_agent`, `list_agents`, or `interrupt_agent` |
| `Skill` | Automatic description match, `/skills`, or `$skillname` |
| `TaskCreate`, `TaskUpdate`, `TaskList` | `update_plan` |
| `AskUserQuestion` | Ask one concise question in chat; do not require `request_user_input` |

Claude named agents are Markdown; Codex named agents are TOML. When no named Codex reviewer exists, pass the body of `agents/staff-reviewer.md`, the scope, and the evidence to a general worker as task instructions, not as a persona.

Both clients discover `hooks/hooks.json` automatically. Commands resolve the plugin with `${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT}}`; Codex provides both variables for compatibility. Users must review and trust plugin hooks before Codex runs them.

Keep both catalogs under marketplace name `development-skills`:

- `.claude-plugin/marketplace.json`: Claude schema with string `source` and `owner.name`.
- `.agents/plugins/marketplace.json`: Codex schema with a local-source object and `interface.displayName`.
