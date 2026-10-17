---
name: obsidian-cli-workspace-and-navigation
description: Use this skill when the user needs official desktop Obsidian CLI workspace, vault, tab, navigation, and utility operations, including workspace save/load/delete, tab and recent-file handling, vault info/listing, random/unique note navigation helpers, web viewer, and wordcount. Keep this skill separate from note CRUD/tasks/properties/history, runtime admin, devtools diagnostics, and Sync/Publish operations.
---

# Obsidian CLI Workspace and Navigation

Use this skill for Obsidian workspace and navigation operations through official desktop `obsidian` CLI commands.

## Routing contract

Use this skill when:
- the user asks about vault metadata or vault listing
- the user asks to inspect or change workspace layout state
- the user asks about tabs, recent files, or opening views/files for navigation
- the user asks for random/unique note navigation helpers
- the user asks to open a URL in Obsidian web viewer
- the user asks for word/character counts

Do not use this skill when:
- the request is primarily note CRUD, tasks, properties, templates, links, or history/diff
- the request is plugin/theme/snippet administration
- the request is Sync or Publish management
- the request is explicitly a named one-command workflow ID (route to `obsidian-cli-workflows`)
- the request is runtime diagnostics, DOM/CSS inspection, screenshot capture, eval, or CDP

## Preconditions

Assume these must be true before relying on this skill:
- `obsidian` command is installed and registered
- Obsidian desktop app is available locally
- first command may launch Obsidian if it is not running
- in Codex Desktop on macOS, direct launches may crash; use the sanitized wrapper

## Codex-safe launcher

In Codex Desktop on macOS, prefer this wrapper:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian ...'
```

Escalate the wrapped command only when required by sandbox boundaries.

## Core operating policy

1. Use only documented official workspace/navigation CLI commands.
2. Prefer read-only inspection first for mixed flows: `vault`, `vaults`, `workspace`, `workspaces`, `tabs`, `recents`, `wordcount`.
3. Treat workspace layout mutations as high-impact operations (`workspace:save`, `workspace:load`, `workspace:delete`).
4. For `tab:open` and `open`, require explicit target intent when both file and view options are plausible.
5. `vault:open` is not currently treated as part of this skill's owned command set in this plugin release.
6. For `web url=...`, require explicit URL target and avoid silent URL construction.
7. Summarize side effects before mutating workspace state.
8. If a request is outside official workspace/navigation surface, say so and stop.

## Risk levels

- low: `vault`, `vaults`, `workspace`, `workspaces`, `tabs`, `recents`, `random`, `random:read`, `wordcount`
- medium: `open`, `tab:open`, `unique`, `web`
- high: `workspace:save`, `workspace:load`, `workspace:delete`

## Response contract

Always return:
- capability used
- risk level (`low`, `medium`, `high`)
- execution mode (`direct` or `escalated`)
- exact command(s) run or proposed
- side-effect summary (for workspace mutations)
- files/views/workspaces affected, if any
- blocking reason, if any

## Command families

Vault:
- `vault`
- `vaults`

Workspace and tabs:
- `workspace`
- `workspaces`
- `workspace:save`
- `workspace:load`
- `workspace:delete`
- `tabs`
- `tab:open`
- `recents`

Navigation and utility:
- `open`
- `random`
- `random:read`
- `unique`
- `web`
- `wordcount`

## References

- `references/obsidian-cli-workspace-navigation-playbook.md`
- `references/limitations-and-boundaries.md`
- `references/validation.md`
- `references/source-links.md`
