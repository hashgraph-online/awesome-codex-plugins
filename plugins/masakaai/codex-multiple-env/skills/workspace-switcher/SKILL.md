---
name: workspace-switcher
description: Set up, inspect, select, or troubleshoot isolated Codex profiles for multiple ChatGPT accounts and workspaces. Use when a user wants to avoid repeated logout/login, keep Personal/Business/Enterprise workspaces separate, inspect official usage windows, or choose the identity used by a future native Codex process.
---

# Masaka Codex Workspace Switcher

Use the Masaka CLI bundled with this plugin. Resolve the plugin root two directories above this file. Prefer an installed `masaka` command; otherwise run `node <plugin-root>/src/cli.mjs` with the same arguments.

## Identity model

Treat one profile as exactly one `(ChatGPT account, ChatGPT workspace)` identity with its own `CODEX_HOME`. Codex owns browser login, token refresh, and credential storage. Masaka stores display metadata and selects which isolated profile a future native Codex process uses.

Direct mode changes only newly started Codex processes. Proxy mode may route the next request of an existing client after onboarding, but never moves an in-flight response to another identity. Do not claim that a running conversation changes account or crosses workspace governance boundaries.

## Workflow

1. Run `masaka doctor` and report missing prerequisites without changing unrelated files.
2. Use `masaka status`, `masaka profiles`, and `masaka usage` for read-only inspection.
3. Use `masaka use <name-or-number>` only after the requested profile is unambiguous. Explain that the selection applies to a future process or, in Proxy mode, the next request.
4. For a new profile, give the user `masaka add [name]` to run in their own terminal so they can complete the official browser login. Verify afterward with `masaka status`.
5. Show `masaka shell-init` when the user wants ordinary `codex` commands to follow the selected profile. Never edit shell startup files unless the user explicitly asks.
6. Use `masaka onboarding` or `masaka proxy on` only when the user explicitly requests the optional local Proxy setup. State that the loopback daemon becomes the sole OAuth refresh owner while Proxy mode is active.

Do not start a nested interactive Codex TUI from an agent tool call. Provide the exact command for the user to run in a new terminal instead.

## Safety boundaries

- Never print, copy, decode for display, or manually edit credential values or `auth.json`.
- Never describe profile switching as a way to bypass service limits or quotas. Usage windows remain authoritative per account and workspace.
- Do not reuse one profile for a different account or workspace. Add a new profile instead.
- Renew a profile only for the same identity and only after its active sessions are closed.
- Deletion requires the user's explicit request and exact-profile confirmation; Masaka moves deleted profiles to recoverable trash.
- Preserve the user's existing Codex configuration, plugins, skills, sessions, and shell setup unless they explicitly request a scoped change.
