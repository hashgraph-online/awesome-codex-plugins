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

| Function | Claude Code | Codex CLI | Cursor IDE | Pi |
|----------|------------|-----------|------------|----|
| Present choices to user | `AskUserQuestion` tool with structured options | Numbered Markdown list as plain text, wait for user reply | Numbered Markdown list (same as Codex) | Numbered Markdown list v1; native UI adapter planned |
| Dispatch subagent | `Agent({ description, prompt, subagent_type })` | Delegate via Codex subagents / typed roles (`explorer`, `worker`) when available; otherwise execute sequentially in the main session | Sequential execution — no parallel subagents. Execute tasks one by one within a single session. | Sequential execution v1. Do not assume native subagents until the Pi SDK dispatcher exists. |
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
  run_in_background: false
})
```

**On Codex CLI / Codex Desktop:**
Delegate the task in detail using the available Codex subagent mechanism when it exists. Map work to these roles:
- **explorer** — read-only evidence gathering (maps to Claude Code's `Explore` subagent)
- **worker** — implementation tasks (maps to Claude Code's `general-purpose` subagent)
- **session-reviewer** — quality review when a dedicated review role is available; otherwise perform the review in the main session

**On Cursor IDE:**
No Agent() tool or typed agent roles. Execute wave tasks sequentially within the active Composer session. After completing each task, report status and move to the next. Parallel execution is not possible — `agents-per-wave` config is ignored on Cursor.

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
