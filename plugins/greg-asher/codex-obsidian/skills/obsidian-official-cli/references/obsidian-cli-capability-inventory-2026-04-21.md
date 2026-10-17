# Obsidian CLI Capability Inventory (2026-04-21)

This inventory captures the official desktop `obsidian` CLI surface available in this environment and maps it against current plugin coverage.

## Snapshot metadata

- Date: 2026-04-21
- Local CLI probe: `obsidian version` -> `1.12.7 (installer 1.12.7)`
- Primary sources:
  - local command help output: `obsidian help` (run via Codex-safe launcher)
  - official docs: https://obsidian.md/help/cli

## Global CLI behavior and targeting model

- Requires desktop Obsidian app and CLI registration.
- Supports one-shot commands and interactive TUI mode.
- `vault=<name|id>` targeting must come before the command.
- `file=<name>` uses wikilink-style name resolution; `path=<path>` is exact vault-relative addressing.
- Many commands default to active file if `file` and `path` are omitted.
- `--copy` can copy command output to clipboard.
- Structured output is available on many commands via `json`, `yaml`, `csv`, `tsv`, or `md` depending on command.

## Capability families and commands

### General

- `help`
- `version`
- `reload`
- `restart`

### Bases

- `bases`
- `base:views`
- `base:create`
- `base:query`

### Bookmarks

- `bookmarks`
- `bookmark`

### Command palette and hotkeys

- `commands`
- `command`
- `hotkeys`
- `hotkey`

### Daily notes

- `daily`
- `daily:path`
- `daily:read`
- `daily:append`
- `daily:prepend`

### File history and diff

- `diff`
- `history`
- `history:list`
- `history:read`
- `history:restore`
- `history:open`

### Files and folders

- `file`
- `files`
- `folder`
- `folders`
- `open`
- `create`
- `read`
- `append`
- `prepend`
- `move`
- `rename`
- `delete`

### Links and graph health

- `backlinks`
- `links`
- `unresolved`
- `orphans`
- `deadends`

### Outline

- `outline`

### Plugins

- `plugins`
- `plugins:enabled`
- `plugins:restrict`
- `plugin`
- `plugin:enable`
- `plugin:disable`
- `plugin:install`
- `plugin:uninstall`
- `plugin:reload`

### Properties

- `aliases`
- `properties`
- `property:set`
- `property:remove`
- `property:read`

### Publish

- `publish:*` commands were not detected in this local CLI build during validation and must be treated as capability-gated.

### Random notes

- `random`
- `random:read`

### Search

- `search`
- `search:context`
- `search:open`

### Sync

- `sync`
- `sync:status`
- `sync:history`
- `sync:read`
- `sync:restore`
- `sync:open`
- `sync:deleted`

### Tags

- `tags`
- `tag`

### Tasks

- `tasks`
- `task`

### Templates

- `templates`
- `template:read`
- `template:insert`

### Themes and CSS snippets

- `themes`
- `theme`
- `theme:set`
- `theme:install`
- `theme:uninstall`
- `snippets`
- `snippets:enabled`
- `snippet:enable`
- `snippet:disable`

### Unique note creation

- `unique`

### Vault

- `vault`
- `vaults`
- `vault:open` was not detected in this local CLI build during validation

### Web viewer

- `web`

### Wordcount

- `wordcount`

### Workspace and tabs

- `workspace`
- `workspaces`
- `workspace:save`
- `workspace:load`
- `workspace:delete`
- `tabs`
- `tab:open`
- `recents`

### Developer commands

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

## Coverage against current plugin catalog

Current plugin-level catalog coverage:

- `obsidian-official-cli`: core note/content workflows
- `obsidian-cli-bases-and-bookmarks`: bases and bookmarks
- `obsidian-cli-runtime-admin`: plugins/themes/snippets/command registry
- `obsidian-cli-devtools`: developer diagnostics and runtime inspection
- `obsidian-cli-sync-and-publish`: sync operations and capability-gated publish workflows
- `obsidian-cli-workspace-and-navigation`: vault/workspace/tab/navigation utilities
- `obsidian-cli-workflows`: named one-command orchestration layer over the six domain skills

The core `obsidian-official-cli` skill remains intentionally narrow and delegates advanced command families to sibling skills.

## Risk and safety notes for advanced surfaces

- Admin-style surfaces (plugins/themes/snippets/restricted mode) can significantly alter vault runtime behavior.
- Sync and capability-gated Publish surfaces require explicit intent due to remote side effects.
- Developer commands can inspect DOM, run JS, and capture screenshots; these need stricter guardrails than plain note edits.
- Existing exact-path mutation safety rules remain valid and should be preserved.
