# Wingman

[English](README.md) | [中文](README.zh-CN.md)

Wingman is a coding-agent plugin with project memory, contract checks, project-map discovery, and focused workflow guidance.

## Install

For Codex:

```bash
codex plugin marketplace add lsshym/wingman.ai
codex plugin add wingman@wingman-marketplace
```

Start a new Codex thread after installation.

For Cursor or Claude Code, use the plugin metadata in this repository. Skill names may appear with a platform namespace, such as `/wingman:memory-setup`.

## Memory Skills

Use these as a simple memory workflow for each repository.

### `memory-setup`

Use once when you want Wingman memory in a repository.

```text
/memory-setup
```

### `memory-load`

Use before meaningful work, especially bug fixes, refactors, business logic, API work, or existing feature changes.

```text
Use `memory-load` before this bug fix.
```

```text
Load Wingman memory before changing the upload flow.
```

### `memory-sync`

Use after meaningful work when the agent should record useful project knowledge.

```text
Use `memory-sync` to record the API contract decision from this change.
```

```text
Sync memory for this bug fix, but do not write unrelated history events.
```

### `memory-clean`

Use only when you explicitly want memory compacted, pruned, deduplicated, or corrected.

```text
Use `memory-clean` to compact the current memory context.
```

## Independent Skills

These skills are separate from the memory workflow. Use them when they fit the task.

### `data-contracts`

Use when connecting APIs, schemas, types, events, configs, data models, CLI inputs, or UI props.

```text
Use `data-contracts` to bind this API response into the existing React component.
```

### `project-map-find`

Use before building something new, or when you need to find whether an existing feature, flow, page, component, module, contract, pattern, or business concept already exists.

```text
Use `project-map-find` before creating a new upload progress component.
```

### `project-map-catalog`

Use after creating or finding one durable project capability that future agents should be able to locate, understand, or reuse as a precedent.

```text
Use `project-map-catalog` for src/components/UploadProgress.tsx.
```

### `using-wingman`

This is Wingman's entry skill for platforms that load plugin-level instructions. You usually do not need to call it directly.

```text
Use `using-wingman` to load the Wingman skill guide.
```

## Slash Aliases

```text
/memory-setup
/project-map-find
/project-map-catalog
```

## Notes

- User instructions and project-local instructions still come first.
- Wingman memory files live inside the current repository under `.wingman/`.
- Wingman project-map files live inside the current repository under `.wingman/project-map/`.
- `memory-setup` and `memory-clean` run only when you directly ask for them.

## License

MIT
