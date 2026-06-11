---
name: bd-first-memory-migration
description: "Run bd first memory migration."
---

# bd-first-memory-migration (Codex twin)

Make `bd` the single source of truth for agent memory: salvage the keepers,
derive the caches, garbage-collect and retire the rest. Three phases, gated
between destructive steps.

## Phases

1. **Audit** (read-only) — inventory every memory layer, classify keepers vs
   junk, and produce the Gate A manifest + reversibility plan. Nothing is
   written. ⛔ Gate A before any mutation.
2. **Migrate** (writes to bd only) — import keepers into bd as typed memories
   with provenance, stand up decay-ranked recall, unify the write path so every
   runtime routes to bd, and regenerate the thin read-only memory-index cache.
3. **GC / Retire** (destructive) — utility scoring, scheduled GC + dedup to a
   cold archive, contradiction/supersede detection, and the hard-retire of dead
   stores with disk reclaim. ⛔ Gate B (rollback test green) + ⛔ Gate C (human
   go/no-go on a live box).

## Guardrails

- Idempotent, reversible, backup-aware; every destructive step offers a dry run.
- Pace bd writes — bulk salvage unpaced can overwhelm a memory-capped server.
- bd-canonical (not br); authored content is archived, never hard-deleted.

## Instructions

Load and follow the skill instructions from the sibling `SKILL.md` file for this skill.
Then read local files in `references/` when needed.
