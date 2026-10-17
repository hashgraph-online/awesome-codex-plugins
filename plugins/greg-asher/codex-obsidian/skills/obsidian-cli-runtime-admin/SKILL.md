---
name: obsidian-cli-runtime-admin
description: Use this skill when the user needs Obsidian runtime administration through official desktop CLI commands for plugins, restricted mode, themes, CSS snippets, command catalog/hotkeys, or targeted command execution. Keep this skill separate from note CRUD, Sync/Publish, and devtools diagnostics.
---

# Obsidian CLI Runtime Admin

Use this skill for Obsidian runtime administration through official desktop `obsidian` CLI commands.

## Routing contract

Use this skill when:
- the user asks to inspect or change plugin state
- the user asks to inspect or change themes or CSS snippets
- the user asks about restricted mode
- the user asks to list command IDs or hotkeys
- the user asks to execute a specific Obsidian command ID

Do not use this skill when:
- the request is primarily note edits, links, tasks, properties, templates, or history
- the request is primarily Sync/Publish operations
- the request is explicitly a named one-command workflow ID (route to `obsidian-cli-workflows`)
- the request is runtime debugging, DOM/CSS inspection, or screenshot/eval diagnostics

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

1. Use only documented official runtime-admin CLI commands.
2. Prefer read-only inventory first for mixed flows: `plugins`, `plugins:enabled`, `themes`, `snippets`, `commands`, `hotkeys`.
3. Treat runtime mutation commands as high impact.
4. For `command id=<...>`, require explicit command ID and do not guess silently.
5. Before mutating runtime state, summarize exact side effects and scope.
6. If command ID, plugin ID, theme name, or snippet name is ambiguous, stop and ask for disambiguation.
7. Do not use this skill as a backdoor to broad opaque behavior; keep execution tied to explicit user request.
8. If a request is outside official runtime-admin support, say so and stop.

## Risk levels

- low: `plugins`, `plugins:enabled`, `plugin`, `themes`, `theme`, `snippets`, `snippets:enabled`, `commands`, `hotkeys`, `hotkey`
- medium: `plugins:restrict`, `command`
- high: `plugin:install`, `plugin:uninstall`, `plugin:enable`, `plugin:disable`, `theme:install`, `theme:uninstall`, `theme:set`, `snippet:enable`, `snippet:disable`

## Response contract

Always return:
- capability used
- risk level (`low`, `medium`, `high`)
- execution mode (`direct` or `escalated`)
- exact command(s) run or proposed
- runtime side-effect summary (if any)
- changed runtime entities (plugin/theme/snippet/command), if any
- blocking reason, if any

## Command families

Plugins:
- `plugins`
- `plugins:enabled`
- `plugins:restrict`
- `plugin`
- `plugin:enable`
- `plugin:disable`
- `plugin:install`
- `plugin:uninstall`
- `plugin:reload`

Themes/snippets:
- `themes`
- `theme`
- `theme:set`
- `theme:install`
- `theme:uninstall`
- `snippets`
- `snippets:enabled`
- `snippet:enable`
- `snippet:disable`

Command palette:
- `commands`
- `command`
- `hotkeys`
- `hotkey`

## References

- `references/obsidian-cli-runtime-admin-playbook.md`
- `references/limitations-and-boundaries.md`
- `references/validation.md`
- `references/source-links.md`
