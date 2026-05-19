---
name: frontmatter-guard
description: Injects the canonical vault frontmatter schema snippet into agent prompts before any vault-write task, preventing malformed YAML frontmatter in Obsidian notes. <example>Context: wave-executor is about to dispatch a vault-mirror agent that writes learning notes under ~/Projects/vault/40-learnings/. user: "dispatch vault-write agent" assistant: "Injecting frontmatter-guard snippet into agent prompt (vault scope detected). Required fields: id, type, created, updated. Enum type: note|daily|project|person|reference|idea|learning|session." <commentary>The wave-executor pre-dispatch hook calls detectVaultTaskScope() — the fileScope contains /Projects/vault/40-learnings/ so the guard triggers and the snippet is prepended to the agent system prompt.</commentary></example>
model: inherit
---

# Frontmatter-Guard Skill

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). Wherever this skill mentions `CLAUDE.md`, the alias rule applies.

## Purpose

vault-mirror and other vault-write agents frequently produce notes with missing or malformed YAML frontmatter — incorrect `type` enum values, missing `id`, wrong date formats. The resulting notes fail the vault-sync validator at session-end, causing hard-gate failures that interrupt the close flow.

This skill solves the problem at the source: it injects the canonical vault frontmatter schema as a Markdown snippet into agent prompts *before* any vault-write task is dispatched. Agents that receive the snippet produce conformant frontmatter on the first attempt, eliminating the validator feedback loop.

## When to Use

Trigger this skill whenever the task being dispatched has vault-write scope. Use the `detectVaultTaskScope()` heuristic from `scripts/lib/frontmatter-guard.mjs` to decide programmatically:

```js
import { readVaultSchema, generateFrontmatterSnippet, detectVaultTaskScope } from './scripts/lib/frontmatter-guard.mjs';

const isVaultTask = detectVaultTaskScope(taskDescription, fileScope);
if (isVaultTask) {
  const schema = readVaultSchema();
  if (schema) {
    const snippet = generateFrontmatterSnippet(schema);
    // prepend snippet to agent system prompt
  }
}
```

The heuristic fires when any of the following is true:

- Any file in `fileScope` contains `/Projects/vault/` in its path.
- Any file in `fileScope` is under a known vault subdirectory: `40-learnings/`, `50-sessions/`, `03-daily/`, `01-projects/`.
- `taskDescription` mentions `vault` or `vault-mirror` AND contains a write-intent keyword (`write`, `create`, `generate`, `emit`, `mirror`, `update`, `add`, `insert`).

`readVaultSchema()` returns `null` when the schema source is missing — the caller must handle this gracefully (skip injection rather than throw).

## How to Invoke

### Programmatic (wave-executor pre-dispatch — deferred to W3-C2)

The canonical call site is the wave-executor pre-dispatch hook. Before spawning an agent whose `fileScope` matches the heuristic, the coordinator calls:

```js
import {
  readVaultSchema,
  computeSchemaHash,
  generateFrontmatterSnippet,
  detectVaultTaskScope,
} from '../../scripts/lib/frontmatter-guard.mjs';

function buildAgentPrompt(basePrompt, taskDescription, fileScope) {
  if (!detectVaultTaskScope(taskDescription, fileScope)) {
    return basePrompt;
  }
  const schema = readVaultSchema(); // null if schema source missing
  if (!schema) return basePrompt;   // graceful fallback

  const snippet = generateFrontmatterSnippet(schema);
  const hash = computeSchemaHash(schema.schemaText);
  return `${snippet}\n\n<!-- frontmatter-guard:${hash} -->\n\n${basePrompt}`;
}
```

The `<!-- frontmatter-guard:<hash> -->` HTML comment records which schema version was injected. It is invisible in rendered Markdown and allows forensic tracing of schema drift.

### Manual (coordinator-direct)

When reviewing a vault-write agent's output, call `generateFrontmatterSnippet()` and paste the result into the task description manually if the auto-dispatch hook is not yet wired.

## Output Contract

`generateFrontmatterSnippet(schema)` returns a deterministic Markdown string with the following sections, in order:

1. **H2 heading** — `## Vault Frontmatter Schema (REQUIRED for files under ~/Projects/vault/)`
2. **Required fields** — inline code list: `id`, `type`, `created`, `updated`
3. **Enums** — `type` (8 values) and optional `status` (7 values) as pipe-separated backtick lists
4. **Field formats** — `id` regex, `tags` nesting convention, date format
5. **Examples** — one fenced YAML block per canonical type: `reference`, `session`, `learning`, `daily`, `project`

The output is stable across calls for the same schema version. Regenerate only when `computeSchemaHash()` returns a different value than the previously injected hash.

## Schema Source Path

The canonical schema source is:

```
~/Projects/projects-baseline/packages/zod-schemas/src/vault-frontmatter.ts
```

`readVaultSchema()` reads this file on every call unless the in-memory mtime cache is current. The function returns `null` (no throw) when the file is absent or unreadable.

The parsed output includes:

| Field | Type | Description |
|---|---|---|
| `typeEnum` | `string[]` | Values of `vaultNoteTypeSchema` z.enum |
| `statusEnum` | `string[]` | Values of `vaultNoteStatusSchema` z.enum |
| `requiredFields` | `string[]` | Always `['id', 'type', 'created', 'updated']` |
| `idRegex` | `string` | Pattern from `slugRegex` in source |
| `tagsRegex` | `string` | Pattern from `tagPathRegex` in source |
| `schemaText` | `string` | Raw source text (used by `computeSchemaHash`) |

## Update Workflow

When the canonical schema source changes (new `type` enum value, new required field, regex adjustment):

1. The mtime cache in `frontmatter-guard.mjs` auto-invalidates — no manual step needed.
2. `readVaultSchema()` re-parses the source on the next call and returns updated values.
3. `generateFrontmatterSnippet()` produces an updated snippet automatically.
4. `computeSchemaHash()` returns a new 8-char hash, which differs from previously-injected hashes in agent prompts — this is the signal that the injected snippet is stale.
5. If the schema adds a new required field or changes enum values in a breaking way, update the five examples in `generateFrontmatterSnippet()` inside `frontmatter-guard.mjs` to reflect the new valid shapes.

Schema drift between the canonical source and vault-sync's vendored inline schema must be resolved in the same commit — see `skills/vault-sync/SKILL.md` § Schema source.

## See Also

- `scripts/lib/frontmatter-guard.mjs` — implementation
- `skills/vault-sync/SKILL.md` — downstream validator (session-end hard gate)
- `skills/vault-mirror/SKILL.md` — primary vault-write consumer
- `skills/wave-executor/SKILL.md` — future call site (W3-C2 wiring)
- `skills/_shared/config-reading.md` — Session Config field reference
