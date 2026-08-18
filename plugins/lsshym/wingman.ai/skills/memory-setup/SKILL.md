---
name: memory-setup
description: Use when the user explicitly invokes `/memory-setup` or explicitly asks to initialize Wingman memory files in the current repository. Do not use for ordinary work, memory loading, memory syncing, or setup of unrelated tools.
---

# Memory Setup

Initialize the Wingman memory workflow for the current repository. Create files on disk; do not merely print templates.

This is an explicit workflow skill. Only proceed when the user directly asks for Wingman memory setup.

## Paths

Use `.wingman/memory/` as the repository-local memory root.

Create:

- `.wingman/memory/`

Seed:

- `.wingman/memory/brief.md`
- `.wingman/memory/context.md`

Initial setup creates only `brief.md` and `context.md`; do not create `domains/` or `history/`.

If `.wingman/memory/` already exists, treat setup as a repair operation: create missing core files, but never overwrite existing user-authored memory files.

## Brief Template

Write `.wingman/memory/brief.md`:

```markdown
# Memory Brief

## 0. Memory Settings
- **Language**: `auto`

## 1. Project Decisions

## 2. Domain Registry
| Domain | Read When | Current File | History Domain Index | History Topics | Aliases | Related Domains | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

Set `Language` to the user's preferred memory language when clear, such as `zh-CN` or `en`. Use `auto` when unclear. Future memory updates should follow this setting.

## Context Template

Write `.wingman/memory/context.md`:

```markdown
# Memory Context

## Pending Tasks

## Current Work

## Short Pointers
```

`domains/` and `history/` are created on demand by `memory-sync`; setup does not seed them or duplicate their templates.

## Finish

Report the created or updated paths.
