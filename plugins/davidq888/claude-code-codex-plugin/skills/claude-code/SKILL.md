---
name: claude-code
description: Use when the user asks for help with Claude Code, the Claude Code CLI, Anthropic coding-agent workflows, prompts to hand off work to Claude Code, or troubleshooting Claude Code setup and terminal usage.
---

# Claude Code

Use this skill when the user wants Codex to help them work with Claude Code.

## Workflow

1. Clarify the user goal only when the target repo, command, or desired handoff is ambiguous.
2. If local setup matters, inspect the environment before giving advice:
   - Check whether `claude` is available with `claude --version`.
   - If this plugin's MCP tools are available, call `claude_code_status` first.
   - Check the current repository state with `git status --short` when operating inside a repo.
   - Read project docs such as `README.md`, `CLAUDE.md`, `AGENTS.md`, or package scripts before suggesting commands.
3. When preparing a handoff prompt for Claude Code, include:
   - The concrete objective.
   - Relevant files or directories.
   - Constraints from the user.
   - Verification steps to run after edits.
4. When troubleshooting, separate setup problems from project problems:
   - Setup: missing CLI, authentication, shell path, permissions, or network access.
   - Project: failing install, failing tests, missing env vars, or unclear repo instructions.
5. Prefer precise terminal commands the user can run directly, and explain what each command proves.

## Account Access

This plugin never stores Claude credentials. It accesses a Claude Code account only through the
local `claude` CLI after the user has authenticated with Anthropic.

Use this setup sequence:

1. Check whether the CLI is installed with `claude_code_status` or `claude --version`.
2. If it is missing on Windows, install it with one of Anthropic's supported commands:
   - `irm https://claude.ai/install.ps1 | iex`
   - `npm install -g @anthropic-ai/claude-code`
3. Call `claude_code_login` to open the official browser login and complete the confirmation.
4. Re-run `claude_code_status`.
5. Use `claude_code_prompt` only after the CLI is installed and authenticated.

## Verification Runs

`claude_code_prompt` runs only in the current Codex task workspace, always starts Claude Code with
`--safe-mode`, and defaults to `manual` permissions. This prevents repository configuration, hooks,
plugins, and MCP configuration from being loaded implicitly.

Use `manual` when each action should ask for approval, or `plan` when the task must remain read-only.
Autonomous modes, including `dontAsk`, `auto`, and `acceptEdits`, are intentionally unavailable
through this plugin. Do not use bypass-permissions modes from this plugin.

To switch accounts or refresh auth, call `claude_code_login`, or run `claude` and use `/login` or `/logout` in the Claude Code session.

## Common Workflows

### Review or second opinion

Use `claude_code_prompt` with `permissionMode: "plan"`. Include the review target, relevant files,
constraints, and expected verification. Ask Claude Code to report findings before suggestions.

### Planned implementation

Use `plan` when the user wants analysis without edits. Use `manual` only when the user explicitly
wants an interactive implementation where every action still requires approval.

### Setup and repair

Run `claude_code_status`, use `claude_code_login` only when authentication needs attention, then
run status again. Keep installation problems separate from project-specific failures.

## Handoff Prompt Template

```text
Goal:
<one concrete outcome>

Context:
- Repo: <path or project name>
- Relevant files: <files/directories>
- Constraints: <user constraints>

Task:
<specific implementation or investigation request>

Verification:
- <command or manual check>
- <command or manual check>
```

## Guardrails

- Do not claim Claude Code has been installed or authenticated unless the local command confirms it.
- Do not invent Claude Code flags. If exact CLI syntax matters and the installed CLI help is unavailable, say what needs checking.
- Keep handoff prompts compact enough to paste into a terminal session.
