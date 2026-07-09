# xedit-knowledgebase.md — retired; see KB records

Retired on 2026-06-02 during KB-5.

The old handwritten xEdit automation knowledgebase has moved into structured
BGS KB records. The file remains at this path so historical links, citations,
and scripts that reference `skills/xedit-automation/xedit-knowledgebase.md`
continue to resolve instead of returning a missing file.

## Current source of truth

- Query live knowledge with the BGS KB MCP tools:
  - `bgs_kb_query` — ranked search across loaded packs.
  - `bgs_kb_get` — fetch one record by id, with per-game variant merging.
  - `bgs_kb_status` — inspect loaded packs, versions, and cache roots.
- Read source records under `knowledge/bgs-kb/packs/core/records/` for
  cross-game xEdit, plugin-format, load-order, and shared engine facts.
- Read per-game records under:
  - `knowledge/bgs-kb/packs/bgs-kb-skyrim/records/`
  - `knowledge/bgs-kb/packs/bgs-kb-fallout4/records/`
  - `knowledge/bgs-kb/packs/bgs-kb-fallout3-fnv/records/`
  - `knowledge/bgs-kb/packs/bgs-kb-starfield/records/`

## Architecture reference

See `docs/internal/superpowers/specs/2026-06-02-agentic-cross-game-kb-design.md`
for the record schema, retrieval design, pack layout, and migration rationale.

## Back-compat note

Some existing KB records and historical plans cite this path as a source because
KB-1 extracted seed records from the old document. Those references are left as
historical provenance; new durable lessons should be authored as KB records, not
appended here.
