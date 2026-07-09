# Claude Code Latest Features Contract

This document is the shared source of truth for Claude Code feature usage across AgentOps skills.

## Baseline

- Target Claude Code release family: `2.1.x`
- Last verified against upstream changelog: `2.1.75`
- Changelog source: `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`

## Current Feature Set We Rely On

### 1. Core Slash Commands

Skills and docs should assume these commands exist and prefer them over legacy naming:

- `/agents`
- `/hooks`
- `/permissions`
- `/memory`
- `/mcp`
- `/output-style`
- `/effort` — set model effort level (low/medium/high). Opus 4.6 defaults to medium.
- `/color` — set prompt-bar color per session (useful for distinguishing parallel sessions)

Reference: `https://code.claude.com/docs/en/slash-commands`

### 2. Agent Definitions

For custom teammates in `.claude/agents/*.md`, use modern frontmatter fields where applicable:

- `model`
- `description`
- `tools`
- `memory` (scope control)
- `background: true` for long-running teammates
- `isolation: worktree` for safe parallel write isolation

Reference: `https://code.claude.com/docs/en/sub-agents`

### 3. Worktree Isolation

When parallel workers may touch overlapping files, prefer Claude-native isolation features first:

- Session-level isolation: `claude --worktree` (`-w`)
- Agent-level isolation: `isolation: worktree`
- Sparse checkout: `worktree.sparsePaths` setting — limit worktree to relevant directories in large monorepos

If unavailable in a given runtime, fall back to manual `git worktree` orchestration.

Reference: changelog `2.1.49`, `2.1.50`, and `2.1.75`.

### 4. Hooks and Governance Events

Hooks-based workflows should include modern event coverage:

- `WorktreeCreate`
- `WorktreeRemove`
- `ConfigChange`
- `SubagentStop`
- `TaskCompleted`
- `TeammateIdle`
- `PostCompact` — fires after session context compaction. Use for auto-recovery (e.g., re-inject context).
- `InstructionsLoaded` — fires when CLAUDE.md loads. Use for policy enforcement.

**HTTP hooks:** Hooks can POST JSON to a URL and receive JSON responses, in addition to shell script execution.

Use these for auditability, policy enforcement, and cleanup.

Reference: `https://code.claude.com/docs/en/hooks`

### 5. Settings Hierarchy

Skill guidance must respect settings precedence:

1. Enterprise managed policy
2. Command-line args
3. Local project settings
4. Shared project settings
5. User settings

Reference: `https://code.claude.com/docs/en/settings`

### 6. Agent Inventory Command

Use `claude agents` as the first CLI-level check to confirm configured teammate profiles before multi-agent runs.

Reference: changelog `2.1.50`.

### 7. Session Management

- `--from-pr <url>` — start or resume a session linked to a specific GitHub PR
- `--worktree` (`-w`) — start session in an isolated git worktree

Reference: `https://code.claude.com/docs/en/cli-reference`

### 8. Tool Enhancements

- **Read tool:** `pages` parameter for PDFs — read specific page ranges (e.g., `pages: "1-5"`). Large PDFs (>10 pages) require this parameter.
- **Bash tool:** Wildcard permission patterns — `Bash(npm *)` or `Bash(* install)` for flexible auto-approval.

### 9. Effort Levels

The `/effort` command controls model reasoning depth:

- `low` — fast, shallow reasoning. Good for research/exploration agents.
- `medium` — balanced (Opus 4.6 default).
- `high` — deep reasoning. Good for implementation and complex debugging.

Skill recommendation: set effort per agent role — low for judges/explorers, high for implementors.

## Skill Authoring Rules

1. Do not reference deprecated permission command names (`/allowed-tools`, `/approved-tools`).
2. Multi-agent skills (`council`, `swarm`, `research`, `crank`, `codex-team`) must explicitly point to this contract.
3. Prefer declarative agent isolation (`isolation: worktree`) over ad hoc branch/worktree shell choreography where runtime supports it.
4. Keep manual `git worktree` fallback documented for non-Claude runtimes.
5. For long-running explorers/judges/workers, document `background: true` as the default custom-agent policy.
6. Use `/effort` to right-size model reasoning per agent role when spawning multi-agent workflows.

## Review Cadence

- Re-verify this contract when:
  - Claude Code changelog introduces new `2.1.x` or `2.2.x` entries
  - any skill adds or changes multi-agent orchestration
  - hook event support changes
