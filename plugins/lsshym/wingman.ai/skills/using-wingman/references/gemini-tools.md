# Gemini CLI Tool Mapping

Skills may use Claude Code tool names. When you encounter these in a skill, use the Gemini CLI equivalent:

| Skill references | Gemini CLI equivalent |
|-----------------|----------------------|
| `Read` (file reading) | `read_file` |
| `Write` (file creation) | `write_file` |
| `Edit` (file editing) | `replace` |
| `Bash` (run commands) | `run_shell_command` |
| `Grep` (search file content) | `grep_search` |
| `Glob` (search files by name) | `glob` |
| `TodoWrite` (task tracking) | `write_todos` |
| `Skill` tool (invoke a skill) | `activate_skill` |
| `WebSearch` | `google_web_search` |
| `WebFetch` | `web_fetch` |
| `Task` tool (dispatch subagent) | `@agent-name` (see [Subagent support](#subagent-support)) |

## Subagent support

Gemini CLI supports subagents natively via the `@` syntax. Use the built-in `@generalist` agent to dispatch a general task when no more specific agent applies.

When a skill says to dispatch a named agent type, use `@generalist` with the full prompt from the skill's prompt template unless the platform provides a matching named agent:

| Skill instruction | Gemini CLI equivalent |
|-------------------|----------------------|
| `Task tool (general-purpose)` with inline prompt | `@generalist` with the inline prompt |
| `Task tool (explorer)` | `@generalist` with the exploration prompt |
| `Task tool (worker)` | `@generalist` with the implementation prompt |
| Code review agent | A bundled review agent if available, otherwise `@generalist` with the full review prompt |

### Prompt filling

Skills may provide prompt templates with placeholders like `{WHAT_WAS_IMPLEMENTED}` or `[FULL TEXT of task]`. Fill all placeholders and pass the complete prompt as the message to the Gemini agent.

### Parallel dispatch

Gemini CLI supports parallel subagent dispatch. When a skill asks for multiple independent subagent tasks in parallel, request all independent `@generalist` or named subagent tasks together. Keep dependent tasks sequential.

## Additional Gemini CLI tools

These tools are available in Gemini CLI but have no Claude Code equivalent:

| Tool | Purpose |
|------|---------|
| `list_directory` | List files and subdirectories |
| `save_memory` | Persist facts to `GEMINI.md` across sessions |
| `ask_user` | Request structured input from the user |
| `tracker_create_task` | Rich task management: create, update, list, and visualize tasks |
| `enter_plan_mode` / `exit_plan_mode` | Switch to read-only research mode before making changes |

## Wingman Notes

- Gemini loads skill metadata at session start and activates full content on demand.
- Wingman does not require subagents by default. Use Gemini subagents only when the user explicitly asks for subagents or the active workflow genuinely requires parallel agent work.
