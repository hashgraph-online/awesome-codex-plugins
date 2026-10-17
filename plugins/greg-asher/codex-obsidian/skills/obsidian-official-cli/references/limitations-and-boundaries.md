# Limitations and Boundaries

## This skill supports

- local desktop Obsidian CLI workflows
- note reading and writing
- note search and search with context
- note structure and links
- tasks
- properties
- templates
- note history and diffs
- practical local vault structure support around those workflows

## This skill does not cover by default

- Obsidian Headless Sync or Publish workflows
- `obsidian://` URI launcher flows
- unofficial community CLIs or wrappers
- custom plugin APIs
- speculative workarounds for unsupported official capabilities
- arbitrary raw note-content editing when a supported Obsidian CLI path exists and the user has not asked for filesystem editing

## Important operational limits

- The official desktop app must be available locally.
- If Obsidian is not already running, the first CLI command may launch it.
- The CLI uses the current working directory vault when applicable; otherwise it falls back to the currently active vault unless `vault=<name|id>` is set.
- `vault=<name|id>` must appear before the command.
- `file=<name>` can be ambiguous when multiple notes share a name.
- Some commands support structured output formats such as `json`, `yaml`, `csv`, or `tsv`; others do not.
- A vault may live outside Codex writable roots, which means mutations may require escalated execution even when reads work.
- `create path=...` may require a local parent-folder creation step before the CLI can succeed.
- Delete and permanent destructive behavior should only happen on explicit user instruction.

## Boundary behavior

When the requested action is outside the supported official desktop CLI surface:
1. say that it is outside scope
2. identify the nearest official capability if one exists
3. stop rather than silently switching tools

If the task is blocked because the official CLI cannot create the needed parent folder or because the execution environment prevents writes:
1. say why the current mutation path is blocked
2. use the smallest safe local vault operation needed to support the CLI path, or request escalated execution when the vault is outside writable roots
3. stop only if the remaining work would require broader raw filesystem editing or another unsupported surface
