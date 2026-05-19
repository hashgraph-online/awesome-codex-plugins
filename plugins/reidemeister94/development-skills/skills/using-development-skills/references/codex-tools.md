# Cross-Platform Reference (Claude Code ↔ Codex)

> **Canonical language: Claude Code.** development-skills SKILL.md bodies use Claude Code tool names, terminology, and flow as the canonical reference. On Codex, translate via the tables below. Skill bodies do NOT contain inline "on CC do X / on Codex do Y" branching — that translation lives here. Other harnesses (Cursor, Copilot, Gemini) not covered yet.

## Install (both CLIs)

Both CLIs install from the same public GitHub marketplace via the native marketplace command. Full user-facing instructions live in the repo root `README.md`; the commands themselves are:

| CLI | Command |
|-----|---------|
| Claude Code | `/plugin marketplace add reidemeister94/development-skills` → `/plugin install development-skills@development-skills` |
| Codex | `codex plugin marketplace add reidemeister94/development-skills` → `codex` → `/plugins` → search → Install |

Claude Code provides both `/plugin install` (in-app) and `claude plugin install` (CLI). Codex installs interactively only — there is no `codex plugin install <name>` one-liner ([docs](https://developers.openai.com/codex/plugins)). The marketplace-add command itself is identical-shaped across both CLIs.

## Tool name map

| Claude Code | Codex equivalent |
|------------------|------------------|
| `Task` (dispatch subagent) | `spawn_agent(agent_type=…, message=…)` |
| Multiple `Task` calls in parallel | Multiple `spawn_agent` calls in the same turn |
| `Task` returns result | `wait_agent(<id>)` returns result |
| `Task` slot freed automatically | `close_agent(<id>)` to free the slot |
| `Skill` tool | Auto-load on description match; `/skills` or `$skillname` mention for explicit invocation |
| `AskUserQuestion` | Numbered list with explicit STOP marker (see below) |
| `Read`, `Write`, `Edit`, `Glob`, `Grep` | Codex native file tools |
| `Bash` | Codex native shell tool |
| `TaskCreate` / `TaskUpdate` / `TaskList` | `update_plan` (Codex consolidates task management) |

## Subagent dispatch on Codex

Codex 0.128+ runs the multi-agent engine (**MultiAgentV2**) by default — there is **no `MultiAgentV2 = true` boolean to flip**. Configure via `[agents]` knobs in `~/.codex/config.toml` if you need to tune budgets:

```toml
[agents]
max_threads = 6                  # default
max_depth = 1                    # default
job_max_runtime_seconds = 1800   # default
```

`spawn_agent`, `wait_agent`, and `close_agent` are exposed as built-in tools when the engine is active (default behavior on 0.128+).

> **Legacy note.** Codex 0.124–0.127 used `[features] multi_agent = true`. That flag is no longer required in stable 0.130. If you see it referenced anywhere in this repo, the doc is stale.

### Dispatch equivalents

| Claude Code | Codex |
|---|---|
| `Task(subagent_type="development-skills:staff-reviewer", prompt=…)` | Read `agents/staff-reviewer.md`, wrap as below, `spawn_agent(agent_type="worker", message=<wrapped>)` |
| `Task(subagent_type="general-purpose", prompt=…)` | `spawn_agent(agent_type="worker", message=<prompt>)` |
| `Task(subagent_type="Explore", prompt=…)` | `spawn_agent(agent_type="explorer", message=<prompt>)` |

### Named-agent dispatch recipe (staff-reviewer)

development-skills ships one named subagent (`staff-reviewer`). Codex subagent definitions use a different format than Claude Code (TOML at `~/.codex/agents/<name>.toml` vs Claude Code's markdown `agents/<name>.md`). Dispatch the portable persona through `spawn_agent`:

1. Read `agents/staff-reviewer.md`.
2. Copy the body (everything after the YAML frontmatter), with placeholders like `{TASK}`, `{GIT_DIFF}`, `{PLAN_FILE_PATH}` already substituted.
3. Wrap using the template below.
4. Spawn a `worker` with the wrapped content as `message`.

```
Your task is to perform the following. Follow the instructions below exactly.

<agent-instructions>
[paste body of agents/staff-reviewer.md, with placeholders filled]
</agent-instructions>

Execute this now. Output ONLY the structured response following the format specified in the instructions above.
```

Framing notes:

- Use **task-delegation framing** ("Your task is…") rather than persona framing ("You are…"). Codex treats `message` as user-level input.
- Wrap instructions in `<agent-instructions>` XML — the model treats tagged blocks as authoritative.
- End with an explicit execution directive.

## AskUserQuestion fallback

`AskUserQuestion` is Claude Code only. When a skill (`brainstorming`, `phase-1-research-plan`, gate questions) tells you to use it, on Codex use a numbered list with an explicit STOP marker:

```
1. [option A] (Recommended)
2. [option B]
3. Other (describe)

Reply with the number or free text. STOP. Wait.
```

End your turn after the list. Do not proceed until the user answers.

## Hooks

`hooks/hooks.json` ships in `development-skills` for SessionStart context injection (the meta-skill body wrapped in `<EXTREMELY-IMPORTANT>`).

- **Claude Code:** loads automatically when the plugin is enabled — no user opt-in.
- **Codex (0.128+):** loads when `[features] plugin_hooks = true` is set in `~/.codex/config.toml`. The `codex_hooks = true` flag from earlier 0.124–0.127 builds is **deprecated** in favor of `plugin_hooks`.

**Known portability gap.** The current `hooks/hooks.json` uses Claude Code's output schema (`hookSpecificOutput.additionalContext` wrapper). Codex 0.124+ reads `hooks/hooks.json` natively but expects a slightly different shape for some sinks. End-to-end hook portability is a separate design problem. On Codex the meta-skill body still auto-loads via description match — **but WITHOUT the `<EXTREMELY-IMPORTANT>` wrapper that the SessionStart hook applies on Claude Code.** The workflow-bypass attractor that hook was authored to mitigate may be stronger on Codex; if you see rationalization-driven phase skipping on Codex, that's likely why.

## What is NOT in this map

- Marketplace UI metadata (`composerIcon`, `brandColor`, screenshots) lives in plugin's `.claude-plugin/plugin.json` `interface{}` block. Not duplicated here.
- Plugin-level details (skills, hooks, MCP server configs) are in `README.md`. This file covers CC↔Codex translation only.
- Cursor / Copilot / Gemini support: not covered. Skill bodies remain Claude-Code-canonical.
