---
name: obsidian-cli-bases-and-bookmarks
description: Use this skill when the user needs official desktop Obsidian CLI Bases or Bookmarks workflows, including base discovery, view/query operations, base item creation, and bookmark management. Keep this skill separate from general note CRUD, runtime admin, Sync/Publish, and devtools diagnostics.
---

# Obsidian CLI Bases and Bookmarks

Use this skill for Obsidian Bases and Bookmarks operations through official desktop `obsidian` CLI commands.

## Routing contract

Use this skill when:
- the user asks to inspect or query `.base` files
- the user asks to list base views or query base results in structured formats
- the user asks to create an item through a base view
- the user asks to list or add bookmarks

Do not use this skill when:
- the request is primarily note CRUD, tasks, templates, link cleanup, or history/diff workflows
- the request is plugin/theme/snippet runtime administration
- the request is Sync/Publish operations
- the request is explicitly a named one-command workflow ID (route to `obsidian-cli-workflows`)
- the request is runtime diagnostics/eval/CDP workflows

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

1. Use only documented official Bases and Bookmarks CLI commands.
2. Prefer read-only discovery first for mixed flows: `bases`, `base:views`, `base:query`, `bookmarks`.
3. Use structured output (`json`, `csv`, `tsv`, `md`, `paths`) whenever supported and useful.
4. Treat `base:create` as a mutating operation and summarize created-file side effects before executing.
5. For `bookmark`, require explicit target type (`file`, `folder`, `search`, or `url`) and avoid silent assumptions.
6. If base file/path, view name, or bookmark target is ambiguous, stop and ask for disambiguation.
7. Keep scope narrow to requested base/bookmark workflow; do not drift into unrelated note-wide edits.
8. If request is outside official Bases/Bookmarks surface, say so and stop.

## Risk levels

- low: `bases`, `base:views`, `base:query`, `bookmarks`
- medium: `bookmark`
- high: `base:create`

## Response contract

Always return:
- capability used
- risk level (`low`, `medium`, `high`)
- execution mode (`direct` or `escalated`)
- exact command(s) run or proposed
- output format used (if structured)
- side-effect summary (for mutating actions)
- files/bookmarks affected, if any
- blocking reason, if any

## Command families

Bases:
- `bases`
- `base:views`
- `base:query`
- `base:create`

Bookmarks:
- `bookmarks`
- `bookmark`

## References

- `references/obsidian-cli-bases-bookmarks-playbook.md`
- `references/limitations-and-boundaries.md`
- `references/validation.md`
- `references/source-links.md`
