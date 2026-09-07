# Platform Tool Reference

> Skills reference this document for platform-specific tool syntax. All platforms share the same skill files — this reference resolves the differences.

## Platform Detection

The current platform is determined by the `scripts/lib/platform.mjs` library:
- `$SO_PLATFORM` = `claude` | `codex` | `cursor` | `pi`
- Environment: `$CLAUDE_PLUGIN_ROOT` (Claude Code), `$CODEX_PLUGIN_ROOT` (Codex CLI), `$CURSOR_RULES_DIR` (Cursor IDE), or `$PI_PLUGIN_ROOT` (Pi)

## Identical Tools (no mapping needed)

These tools have the same name and behavior on all platforms. Cursor IDE uses equivalent built-in tools for file operations and terminal commands.
- **Read** — read file contents
- **Write** — create/overwrite files
- **Edit** — string replacement in files
- **Bash** — execute shell commands
- **Glob** — file pattern matching
- **Grep** — content search (ripgrep)

## Platform-Specific Tool Mapping

> **Every statement about a foreign platform carries a measurement date and the tool version it was measured on** (PSA-006). An undated capability claim about Codex CLI, Cursor IDE, or Pi is unverified — re-measure before relying on it, and stamp what you find.

| Function | Claude Code | Codex CLI | Cursor IDE | Pi |
|----------|------------|-----------|------------|----|
| Present choices to user | `AskUserQuestion` tool with structured options | Numbered Markdown list as plain text, wait for user reply | Numbered Markdown list (same as Codex) | Numbered Markdown list v1; native UI adapter planned |
| Dispatch subagent | `Agent({ description, prompt, subagent_type })` | Native multi-agent collaboration namespace: `spawn_agent`, `list_agents`, `wait_agent`, `send_message`, `followup_task`, `interrupt_agent`, `close_agent`. Measured 2026-08-25 on `codex-cli 0.141.0` — `codex features list` → `multi_agent  stable  true`. | No native in-session Agent tool. Coordinator-side foreign dispatch via the headless `cursor-agent` CLI exists (`scripts/lib/wave-executor/foreign-dispatch.mjs`, #1150) — measured 2026-08-25 on `cursor-agent 2026.08.11-e8db854`. | Sequential execution v1. Do not assume native subagents until the Pi SDK dispatcher exists. |
| Track tasks | `TaskCreate` / `TaskUpdate` / `TaskList` | Plain-text checklist in response context | Plain-text checklist (same as Codex) | Plain-text checklist (same as Codex) |
| Enter plan mode | `EnterPlanMode` / `ExitPlanMode` tools | `/plan` slash command (prompt-level, not tool-based) | Instruction-based: "Focus on analysis and planning. Do not modify files until the user approves." | `/plan` prompt template; use instruction-based planning when tool mode is unavailable |
| Web search | `WebSearch` tool | Built-in web search (invoke via instruction) | `@web` in Cursor chat | Use Pi's available web/search tools if configured; otherwise Bash curl or browser handoff |
| Web fetch | `WebFetch` tool | Not available natively; use MCP or Bash curl | Bash curl (same as Codex) | Bash curl or configured Pi tool |

## AskUserQuestion Fallback Pattern

When a skill instructs "Use the AskUserQuestion tool", apply this pattern:

**On Claude Code:** Use the AskUserQuestion tool with structured options as documented.

**On Codex CLI / Cursor IDE / Pi:** Present the same choices as a numbered Markdown list and ask the user to respond:
```
Choose one:
1. Option A — description
2. Option B — description  
3. Option C — description

Reply with the number of your choice.
```

## Agent Dispatch Pattern

**On Claude Code:**
```
Agent({
  description: "3-5 word summary",
  prompt: "full task context...",
  subagent_type: "general-purpose",
  run_in_background: true   // RECOMMENDED for wave dispatch since 2026-08-25 (FA-6);
                            // verify the started set via meta.json sidecars, never via the
                            // launch ack — see skills/wave-executor/wave-loop.md § Started-Set Verification
})
```

**On Codex CLI / Codex Desktop:**
Codex has a native multi-agent collaboration namespace — use it; do not fall back to sequential in-session execution. Measured 2026-08-25 on `codex-cli 0.141.0`: `codex features list` reports `multi_agent  stable  true`, and a tool-call census over `~/.codex/sessions` (`grep -rhoE '"(spawn_agent|send_message|wait_agent|list_agents|followup_task|interrupt_agent|close_agent)"' . | sort | uniq -c`) returns wait_agent 6041 · send_message 2233 · spawn_agent 1748 · list_agents 836 · close_agent 781 · followup_task 656 · interrupt_agent 109 — i.e. the toolset is in routine production use, not a preview.

Lifecycle: `spawn_agent` (launch, one per wave task) → `list_agents` (enumerate the started set) → `wait_agent` (block on completion) → `send_message` / `followup_task` (steer a running agent) → `interrupt_agent` / `close_agent` (abort / reap). Verify the started set via `list_agents`, never via the `spawn_agent` return alone. Map wave work to these prompt-level roles:
- **explorer** — read-only evidence gathering (maps to Claude Code's `Explore` subagent)
- **worker** — implementation tasks (maps to Claude Code's `general-purpose` subagent)
- **session-reviewer** — quality review; spawn as a separate agent rather than reviewing in the main session

**On Cursor IDE:**
No native Agent() tool or typed agent roles inside the Composer session — wave tasks run sequentially there, and `agents-per-wave` is ignored. This is a statement about the IDE session only: coordinator-side foreign dispatch to Cursor models via the headless `cursor-agent` CLI does exist (`scripts/lib/wave-executor/foreign-dispatch.mjs`, #1150 — detached worktree, filesystem-measured result, `orchestrator.foreign_dispatch.completed` telemetry, mandatory Claude review, `NEVER_FOREIGN_ROLES` lock). Measured 2026-08-25 on `cursor-agent 2026.08.11-e8db854`. Slash commands live in `.cursor/commands/`. There is no Skill tool — Read `skills/<name>/SKILL.md` instead.

**On Pi:**
No Session Orchestrator Pi subagent dispatcher exists in v1. Execute wave tasks sequentially in the active Pi session. Treat `agents-per-wave` as advisory until the SDK-based dispatcher lands.

## Model Preference Mapping

| Claude Code | Codex CLI | Cursor IDE | Pi | Use Case |
|------------|-----------|------------|----|----------|
| opus | gpt-5.4 | claude-opus-4-6 | active Pi model | Complex reasoning, architecture, session coordination |
| sonnet | gpt-5.4-mini | claude-sonnet-4-6 | active Pi model | Implementation, review, routine tasks |
| haiku | gpt-5.4-mini | claude-sonnet-4-6 | active Pi model | Simple lookups, fast checks |

Skills use `model-preference` (Claude), `model-preference-codex` (Codex), `model-preference-cursor` (Cursor), and active-model fallback on Pi in YAML frontmatter.

## State Directory

- **Claude Code:** `.claude/` (STATE.md, wave-scope.json)
- **Codex CLI:** `.codex/` (STATE.md, wave-scope.json)
- **Cursor IDE:** `.cursor/` (STATE.md, wave-scope.json)
- **Pi:** `.pi/` (STATE.md, wave-scope.json)
- **Shared:** `.orchestrator/metrics/` (sessions.jsonl, learnings.jsonl) — all platforms read and write here

## Config File

- **Claude Code:** Session Config in `CLAUDE.md` under `## Session Config`
- **Codex CLI:** Session Config in `AGENTS.md` under `## Session Config`
- **Cursor IDE:** Session Config in `CLAUDE.md` under `## Session Config` (Cursor reads CLAUDE.md natively — no separate config file)
- **Pi:** Session Config in `AGENTS.md` under `## Session Config` preferred; `CLAUDE.md` remains supported by the shared alias rule
- Format is identical on all platforms.
