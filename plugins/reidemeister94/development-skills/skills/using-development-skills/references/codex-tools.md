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
- **Codex (0.131+):** loads automatically when the plugin is enabled — no flag needed. PR #22549 enabled `plugin_hooks` by default in the 0.131 stable cut (2026-05-18).
- **Codex (0.128–0.130, legacy):** loads only when `[features] plugin_hooks = true` is set in `~/.codex/config.toml`. The flag is a no-op on 0.131+ — keeping it there does no harm, but it carries no signal either.
- **Codex (0.124–0.127, legacy):** used `[features] codex_hooks = true`. **Deprecated.** Upgrade to 0.131+ or set `plugin_hooks = true` if you must stay on 0.128–0.130.

`hooks/hooks.json` resolves bundled scripts with `${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT}}`: Claude Code sets `CLAUDE_PLUGIN_ROOT`; Codex sets `PLUGIN_ROOT` and also `CLAUDE_PLUGIN_ROOT` for compat. The namespaced var is preferred (a stray generic `PLUGIN_ROOT` in the user env can't shadow it on Claude Code); the generic `PLUGIN_ROOT` is the fallback for older Codex that left `CLAUDE_PLUGIN_ROOT` empty. `SessionStart`'s `hookSpecificOutput.additionalContext` shape is identical on both harnesses, so the `<EXTREMELY-IMPORTANT>` wrapper is injected on both when plugin hooks are enabled and trusted. Other events' output shapes still differ — see `.agents/rules/formatting-hooks.md`.

## Marketplace files (for plugin maintainers)

Two marketplace catalogs live in the repo:

| File | Schema | Read by |
|---|---|---|
| `.claude-plugin/marketplace.json` | Claude Code (`source` is bare string, `owner.name` required) | Claude Code |
| `.agents/plugins/marketplace.json` | Codex (`source` is object `{source: "local", path: "…"}`, `interface.displayName` required) | Codex |

Both list the same plugin under the same marketplace `name` (`development-skills`). When the plugin metadata changes, update **both** files. See `.agents/rules/plugin-packaging.md`.

## What is NOT in this map

- Marketplace UI metadata (`composerIcon`, `brandColor`, screenshots) lives in the plugin's `.codex-plugin/plugin.json` `interface{}` block. Not duplicated here.
- Plugin-level details (skills, hooks, MCP server configs) are in `README.md`. This file covers CC↔Codex translation only.
- Cursor / Copilot / Gemini support: not covered. Skill bodies remain Claude-Code-canonical.
