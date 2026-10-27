---
name: omos-retro
description: "Retrospect a finished run via $oh-my-openspec:omos-retro — compile the evidence bundle, dispatch the retrospector, relay ≤8 cited findings. Read-only. Invoke via $oh-my-openspec:omos-retro."
---

> Codex host adaptation (generated from skills/omos-retro/SKILL.md — source of truth stays there):
> - Dispatch roles with `spawn_agent` / `send_input` / `wait_agent` / `close_agent`. Subagents are asynchronous (default up to 6 concurrent threads), so a wave is one batch of `spawn_agent` calls followed by `wait_agent` collection — never poll.
> - `openspec_validate` is provided by this plugin's bundled MCP server as `mcp__openspec__openspec_validate` — call it with `cwd` set to your session's project directory (the `change` filter optional); the VALID/INVALID/UNAVAILABLE/ERROR one-look report format is identical to OpenCode.
> - This skill is invoked as a `$oh-my-openspec:omos-retro` mention (or picked from /skills). There is no argument substitution: arguments arrive as plain text in the user's message after the mention — read them from there; when absent, follow this skill's elicitation steps.
> - Roles run from `~/.codex/agents/omos-*.toml`. If `spawn_agent` reports an unknown agent, stop and tell the user to run `$oh-my-openspec:omos-setup` once.

# omos-retro

Mine the current session for defects in the plugin's own prompts. Read-only:
this command never edits anything — findings are for a future PR.

## Flow

### 1. Compile the evidence bundle

From the current session, assemble exactly:

- commands run (`$oh-my-openspec:omos-init`, `$oh-my-openspec:omos-plan`, `$oh-my-openspec:omos-apply`,
  `$oh-my-openspec:omos-archive`) and
  their targets;
- every role dispatch: role, one-line task, final report verbatim;
- friction lines: `BLOCKED:`, `FAIL`, `NEEDS-FIX`, re-dispatches, extra
  critic/verify rounds, user corrections ("no, I meant…");
- `git diff --stat` at the end of the run.

Keep the bundle raw — quoted lines, not your paraphrase of them. The
retrospector's findings must be quotable from it.

### 2. Dispatch

Send the bundle to `omos-retrospector` verbatim. One dispatch, no
rounds: the role either returns findings or `No findings — run clean.`

### 3. Relay

Present the report as-is. Add nothing — no commentary, no severity
re-shuffling, no "suggestions". Present the report as rendered Markdown,
never inside a code block. If the user wants fixes, that is ordinary
work in the plugin's own repository (`$oh-my-openspec:omos-plan` there, or direct
edits), not an action of this command.

## Guardrails

- Never edit `agents/`, `skills/`, `core/`, or any project file from this
  command.
- The bundle is the only evidence: do not feed the retrospector
  interpretations, and do not fill gaps from memory.
- An empty run (no role dispatches) → say so and stop; do not invent a
  session to analyze.
