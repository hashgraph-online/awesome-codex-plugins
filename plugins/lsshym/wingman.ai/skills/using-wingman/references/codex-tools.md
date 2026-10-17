# Codex Tool Mapping

Skills may use Claude Code tool names. When you encounter these in a skill, use the Codex equivalent:

| Skill reference | Codex equivalent |
|-----------------|------------------|
| `Task` tool (dispatch subagent) | `spawn_agent` (see [Subagent dispatch requires multi-agent support](#subagent-dispatch-requires-multi-agent-support)) |
| Multiple `Task` calls (parallel) | Multiple `spawn_agent` calls |
| Task returns result | `wait_agent` |
| Task completes automatically | `close_agent` to free slot |
| `TodoWrite` (task tracking) | `update_plan` |
| `Skill` tool (invoke a skill) | Skills load natively; just follow the instructions |
| `Read`, `Write`, `Edit` (files) | Use native file tools; for manual edits, prefer `apply_patch` |
| `Grep`, `Glob` (search) | Use `rg`, `rg --files`, or native search tools |
| `Bash` (run commands) | `exec_command` |

## Subagent dispatch requires multi-agent support

Codex subagents require multi-agent support. If `spawn_agent`, `wait_agent`, or `close_agent` are not available, continue in the main session and explain the limitation when it affects the requested workflow.

When available, Codex may require this config in `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

Legacy note: Codex builds before `rust-v0.115.0` exposed spawned-agent waiting as `wait`. Current Codex uses `wait_agent` for spawned agents. The `wait` name now belongs to code-mode `exec/wait`, which resumes a yielded exec cell by `cell_id`; it is not the spawned-agent result tool.

## Environment Detection

Skills that create worktrees or finish branches should detect their environment with read-only git commands before proceeding:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` -> already in a linked worktree; skip creation.
- `BRANCH` empty -> detached HEAD; cannot branch, push, or PR from the sandbox.

## Codex App Finishing

When the sandbox blocks branch or push operations, such as detached HEAD in an externally managed worktree, the agent should commit all work it can commit and inform the user to use the app's native controls:

- **Create branch**: names the branch, then commits, pushes, or opens the PR through the app UI.
- **Hand off to local**: transfers work to the user's local checkout.

The agent can still run tests, stage files, and provide suggested branch names, commit messages, and PR descriptions.

## Wingman Notes

- Wingman does not require subagents by default. Use Codex subagents only when the user explicitly asks for subagents or the active workflow genuinely requires parallel agent work.
- Respect Codex sandbox and escalation requirements for shell commands.
