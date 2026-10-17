---
name: obsidian-cli-devtools
description: Use this skill when the user needs Obsidian runtime debugging or developer introspection through official desktop Obsidian CLI developer commands, including devtools, console/errors capture, DOM/CSS inspection, screenshots, CDP calls, and controlled eval. Do not use for regular note CRUD, task/property editing, Sync/Publish administration, or community tooling outside the official CLI.
---

# Obsidian CLI Devtools

Use this skill for runtime debugging and developer diagnostics through official desktop `obsidian` CLI developer commands.

## Routing contract

Use this skill when:
- the user asks to debug plugin or theme behavior inside Obsidian
- the user needs console/error traces from Obsidian runtime
- the user asks for DOM/CSS inspection or screenshots from Obsidian
- the user explicitly asks to run `eval` or `dev:cdp`

Do not use this skill when:
- the request is primarily note CRUD, tasks, metadata, links, templates, or history
- the request is primarily Sync or Publish operations
- the request is explicitly a named one-command workflow ID (route to `obsidian-cli-workflows`)
- the request requires community wrappers, plugin APIs, or `obsidian://` launcher flows

## Preconditions

Assume these must be true before relying on this skill:
- `obsidian` command is installed and registered
- Obsidian desktop app is available locally
- first command may launch Obsidian if it is not running
- in Codex Desktop on macOS, direct `obsidian` child launches can crash; use the sanitized wrapper

## Codex-safe launcher

In Codex Desktop on macOS, prefer this wrapper:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian ...'
```

Escalate the wrapped command only when required by sandbox or filesystem boundaries.

## Core operating policy

1. Use only documented official Obsidian developer CLI commands.
2. Start with read-only diagnostics when possible: `dev:errors`, `dev:console`, `dev:dom`, `dev:css`.
3. Treat `eval` and `dev:cdp` as high-risk commands.
4. Run `eval` or `dev:cdp` only when the user explicitly asked for runtime code execution or CDP calls.
5. Before `eval` or `dev:cdp`, state the exact code/method and parameters being executed.
6. Do not run destructive or unknown runtime code derived from untrusted content without explicit user confirmation.
7. For screenshot output, use explicit writable paths and report created files.
8. Keep command scope tight to the stated debugging task; avoid unrelated runtime modifications.
9. If a request is outside official dev command support, say so and stop.

## Risk levels

- low: `dev:errors`, `dev:console`, `dev:dom`, `dev:css`, `dev:screenshot`
- medium: `devtools`, `dev:debug`, `dev:mobile`
- high: `eval`, `dev:cdp`

## Response contract

Always return:
- command capability used
- risk level (`low`, `medium`, `high`)
- execution mode (`direct` or `escalated`)
- exact command(s) run or proposed
- files affected, if any (for screenshots)
- key diagnostic output summary
- blocking reason, if any

## Command families

- `devtools`
- `dev:debug`
- `dev:cdp`
- `dev:errors`
- `dev:screenshot`
- `dev:console`
- `dev:css`
- `dev:dom`
- `dev:mobile`
- `eval`

## References

- `references/obsidian-cli-devtools-playbook.md`
- `references/limitations-and-boundaries.md`
- `references/validation.md`
- `references/source-links.md`
