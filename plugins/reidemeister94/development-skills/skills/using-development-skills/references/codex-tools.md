# Cross-Platform Reference (Claude Code ↔ Codex)

SKILL.md bodies use Claude Code tool names and flow as canonical; translate to Codex via the maps below. Skill bodies carry no inline CC/Codex branching — it lives here.

## Install

Same public GitHub marketplace for both CLIs (prereqs in repo root `README.md`); Codex installs per-plugin interactively only ([docs](https://developers.openai.com/codex/plugins)).

## Tool name map

| Claude Code | Codex |
|---|---|
| `Task` (dispatch subagent) | `spawn_agent(agent_type=…, message=…)` |
| Parallel `Task` calls | Multiple `spawn_agent` in the same turn |
| `Task` returns result | `wait_agent(<id>)` returns result; `close_agent(<id>)` frees the slot |
| `Skill` | Auto-load on description match; `/skills` or `$skillname` for explicit invocation |
| `AskUserQuestion` | Numbered list with STOP marker (see below) |
| `TaskCreate` / `TaskUpdate` / `TaskList` | `update_plan` |

## Subagent dispatch on Codex

Codex 0.128+ runs the multi-agent engine (**MultiAgentV2**) by default — there is **no `MultiAgentV2 = true` flag**. `spawn_agent` / `wait_agent` / `close_agent` are built-in when active. Tune budgets via `~/.codex/config.toml`:

```toml
[agents]
max_threads = 6                  # default
max_depth = 1                    # default
job_max_runtime_seconds = 1800   # default
```

| Claude Code | Codex |
|---|---|
| `Task(subagent_type="development-skills:staff-reviewer", prompt=…)` | Read `agents/staff-reviewer.md`, wrap (recipe below), `spawn_agent(agent_type="worker", message=<wrapped>)` |
| `Task(subagent_type="general-purpose", prompt=…)` | `spawn_agent(agent_type="worker", message=<prompt>)` |
| `Task(subagent_type="Explore", prompt=…)` | `spawn_agent(agent_type="explorer", message=<prompt>)` |

### Named-agent dispatch recipe (staff-reviewer)

Codex subagents use TOML at `~/.codex/agents/<name>.toml`, not Claude Code's markdown. Dispatch the portable persona through `spawn_agent`: read `plugins/development-skills/agents/staff-reviewer.md`, take the body after the frontmatter and supply the agent's inputs (Task, Git diff, Plan file path, etc. — stated in prose under `## Inputs`), wrap, and spawn a `worker` with the wrapped content as `message`:

```
Your task is to perform the following. Follow the instructions below exactly.

<agent-instructions>
[paste body of agents/staff-reviewer.md, with its inputs supplied]
</agent-instructions>

Execute this now. Output ONLY the structured response following the format specified in the instructions above.
```

Use task-delegation framing ("Your task is…"), not persona framing — Codex treats `message` as user-level input.

## AskUserQuestion fallback

Claude Code only. On Codex, use a numbered list with an explicit STOP marker, then end your turn:

```
1. [option A] (Recommended)
2. [option B]
3. Other (describe)

Reply with the number or free text. STOP. Wait.
```

## Hooks

`hooks/hooks.json` ships in `development-skills` for SessionStart context injection (meta-skill body wrapped in `<EXTREMELY-IMPORTANT>`).

- **Claude Code:** auto-loads when the plugin is enabled.
- **Codex (0.131+, current stable 0.140):** auto-loads when enabled — no feature flag. (Legacy `[features] plugin_hooks` / `codex_hooks` flags from 0.124–0.130 are obsolete; see `.agents/rules/formatting-hooks.md`.)

`hooks/hooks.json` resolves bundled scripts with `${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT}}`: Claude Code sets `CLAUDE_PLUGIN_ROOT`; Codex sets both. The namespaced var is preferred so a stray generic `PLUGIN_ROOT` in the user env can't shadow it; `PLUGIN_ROOT` is the fallback for older Codex that left `CLAUDE_PLUGIN_ROOT` empty. `SessionStart`'s `hookSpecificOutput.additionalContext` shape is identical on both; other events differ — see `.agents/rules/formatting-hooks.md`.

## Marketplace files (for plugin maintainers)

Both catalogs list the same plugin under marketplace `name` `development-skills`; update **both** when the plugin metadata changes (see `.agents/rules/plugin-packaging.md`):

- `.claude-plugin/marketplace.json` — Claude Code schema (`source` bare string, `owner.name` required).
- `.agents/plugins/marketplace.json` — Codex schema (`source` object `{source:"local", path:"…"}`, `interface.displayName` required).
