---
name: obsidian-official-cli
description: Use this skill when the user wants local Obsidian note or metadata work done primarily through documented official desktop `obsidian` CLI commands, with limited local vault filesystem support when needed for parent folders, path checks, ambiguity resolution, verification, or safe vault structure operations. Best for local vault search, note reads, exact-path note updates, backlinks, tasks, properties, templates, and local history. Do not use it for runtime admin, devtools diagnostics, workspace/navigation administration, community tools, `obsidian://` launcher tasks, Headless Sync or Publish workflows, or plugin-specific APIs.
---

# Obsidian Official CLI

Use this skill for local Obsidian vault work through the official desktop `obsidian` CLI only.

## Routing contract

Use this skill when:
- the user explicitly wants the official desktop Obsidian CLI
- the task is local vault note, link, task, property, template, or local history work
- the request can be satisfied with documented `obsidian` commands

Do not use this skill when:
- the request is primarily arbitrary markdown editing rather than an Obsidian workflow
- the request is about Headless Sync, Publish, or any non-desktop official surface
- the request is about runtime admin, devtools diagnostics, or workspace/navigation administration
- the request is explicitly a named one-command workflow ID (route to `obsidian-cli-workflows`)
- the request is about `obsidian://` launchers, plugin APIs, or community tooling

## Preconditions

Assume these must be true before relying on this skill:
- the `obsidian` command is installed and on the system path
- Obsidian desktop CLI has been enabled and registered
- the desktop app is available locally
- the first CLI command may launch Obsidian if it is not already running
- the target vault path may live outside Codex writable roots, which changes how mutations must be executed
- in Codex Desktop on macOS, direct `obsidian ...` child-process launches may inherit app identity variables from Codex and crash during AppKit / LaunchServices registration

## Codex Desktop launch rule

When this skill is used from Codex Desktop on macOS, do **not** invoke `obsidian` directly first. Prefer the Codex-safe wrapper form below:

```bash
script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian ...'
```

Why:
- direct launches from the Codex app environment can crash before CLI handling begins
- the crash is caused by inherited Cocoa / app identity state, not by vault permissions or note content
- the sanitized `script + login shell` wrapper has been validated to run `obsidian version` and real CLI commands from Codex successfully

If the user is in a normal terminal outside Codex, plain `obsidian ...` may still work fine.

## Execution mode rule

Separate these two decisions:

- command form: in Codex Desktop on macOS, use the sanitized wrapper instead of raw `obsidian ...`
- privilege mode: use normal in-sandbox execution unless the wrapped command fails for write-permission reasons or a required support step cannot run in-sandbox

When escalation is required, escalate the **wrapped** command, not the raw `obsidian` command.

Enhanced wrapped execution form:

```text
functions.exec_command(
  cmd="script -q /dev/null /usr/local/bin/zsh -ilc 'unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; obsidian vault=<vault> <command>'",
  sandbox_permissions="require_escalated",
  justification="<short user-facing reason>",
  prefix_rule=["script","-q","/dev/null","/usr/local/bin/zsh","-ilc"]
)
```

Use this enhanced form when:
- the target vault is outside writable roots and the wrapped CLI mutation fails for write-permission reasons
- a supporting filesystem step for the vault workflow requires escalation
- GUI-app launch or IPC access is blocked by the Codex sandbox and the wrapped command is important to the user's request

## Core operating policy

1. Use only documented official Obsidian CLI commands and parameters.
2. If `vault=` is used, place it first before the command.
3. Classify the target as one of: `active-file`, `resolved-file`, `exact-path`, `daily-note`, `ambiguous`, or `none`.
4. Use read-only resolution first when the file target is unclear.
5. Use `file=` only for loose read-only note resolution.
6. Once the exact note is known, switch to `path=` for subsequent commands.
7. Never mutate note content with `file=` or against an ambiguous target.
8. Never mutate note content through implicit active-file behavior.
9. Note-content mutations require either an exact `path=` or an explicit documented daily-note command such as `daily:append` or `daily:prepend`.
10. Use minimal local filesystem operations to support the CLI when needed: check path existence, list files or folders, create missing parent folders, verify results on disk, and perform safe non-content vault structure operations.
11. Prefer the official CLI for note-content work even when filesystem support is available.
12. Prefer structured output when the command documents `json`, `yaml`, `csv`, or `tsv`.
13. Before the first mutation in a session, run a lightweight read-only probe such as `obsidian version`, `read`, or `daily:read` to confirm the CLI and app are responsive. In Codex Desktop on macOS, run that probe through the sanitized launch wrapper, not through a direct `obsidian` child process.
14. If the target vault is outside Codex writable roots, try the wrapped CLI mutation first when that path is available. Request escalated execution only if the wrapped CLI mutation fails for write-permission reasons or if a required supporting shell operation cannot run in-sandbox.
15. If a direct launch crashes from Codex Desktop on macOS, retry through the sanitized launch wrapper before concluding the CLI is unavailable.
16. If the wrapped command still fails and the task is important, retry the wrapped command with escalated execution before concluding the CLI is unavailable.
17. If the sanitized wrapper also fails under escalation on the initial read-only probe, stop and tell the user to open Obsidian manually before retrying.
18. If broader local filesystem work would go beyond safe support operations, only do it when the user explicitly wants that broader approach.
19. If a capability is outside the official desktop CLI surface, say so plainly and stop.

## Resolution policy

- If the request already provides an exact vault-relative path, use `path=` immediately.
- If the request is specifically about today's daily note, use the documented `daily:*` command family and classify the target as `daily-note`.
- If the request only provides a note name, resolve read-only first with search or file discovery.
- If multiple notes could match, surface the ambiguity and stop before any mutation.
- If no file or path is supplied, only read-only commands may act on the active file.
- If a documented CLI mutation needs a missing parent folder, use the smallest safe step that makes the CLI path succeed. If the CLI works directly, keep using it. If it fails specifically because the parent folder is missing, create the parent folder locally and retry.

## Response contract

Always return:
- the official Obsidian capability used
- the target mode: `active-file`, `resolved-file`, `exact-path`, `daily-note`, `ambiguous`, or `none`
- the execution mode: direct or escalated
- whether local filesystem support was used
- the exact command or commands proposed or run
- whether structured output was used when available
- the files affected, if any
- why escalation was required, when escalation is used
- the blocking reason when clarification or refusal is required

## Command families

Read and inspect:
- `read`
- `file`
- `files`
- `folder`
- `folders`
- `outline`
- `search`
- `search:context`

Create and modify:
- `create`
- `append`
- `prepend`
- `daily`
- `daily:path`
- `daily:read`
- `daily:append`
- `daily:prepend`
- `move`
- `rename`
- `delete`

Links and structure:
- `backlinks`
- `links`
- `unresolved`
- `orphans`
- `deadends`

Tasks and metadata:
- `tasks`
- `task`
- `properties`
- `property:read`
- `property:set`
- `property:remove`
- `aliases`
- `tags`

Templates and history:
- `templates`
- `template:read`
- `template:insert`
- `history`
- `history:list`
- `history:read`
- `history:restore`
- `diff`

## References

For command patterns, capability examples, and manual validation workflows, use:
- `references/obsidian-cli-command-playbook.md`
- `references/capability-cookbook.md`
- `references/limitations-and-boundaries.md`
- `references/validation.md`
- `references/maintenance-notes.md`
- `references/source-links.md`
