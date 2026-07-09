---
name: sync-memory
description: "Batch sync session learnings to memory. Use when: persisting campaign insights and performance history across sessions."
---

# /digital-marketing-pro:sync-memory

## Purpose

Batch sync current session learnings, insights.json entries, and campaign history to the persistent memory layer. Ensures valuable knowledge from this session is preserved for future sessions without requiring the user to manually save each item via `/digital-marketing-pro:save-knowledge`. Syncs incrementally — only new items since the last sync checkpoint — so repeated syncs are fast, idempotent, and safe. Handles the full pipeline from diff detection through storage to checkpoint update, with detailed reporting on what was synced, skipped, or failed. Run this before ending a productive session to capture everything worth remembering.

## Input Required

The user must provide (or will be prompted for):

- **Sync scope**: What to sync — `all` (insights + campaigns + session learnings), `insights-only` (only insights.json entries — performance data, metric snapshots, and automated learnings), or `campaigns-only` (only campaign data, retrospective learnings, and strategy decisions). Default is `all`
- **Force full sync (optional)**: Set to `true` to ignore the last sync checkpoint and re-sync everything regardless of previous sync state. Useful after data corruption, vector DB migration, index rebuild, or when the local index and persistent storage may be out of alignment. Default is `false` (incremental sync from last checkpoint)
- **Content type override (optional)**: Force a specific content_type classification for all synced items — overrides auto-detection. Rarely needed but useful for bulk re-classification when migrating knowledge taxonomy
- **Dry run (optional)**: Set to `true` to preview what would be synced without actually storing anything. Shows the full diff, payload previews, and estimated storage impact for review before committing. Useful for auditing what has accumulated since the last sync
- **Tags to apply (optional)**: Additional tags to apply to all items in this sync batch — e.g., "q1-2026-review", "pre-rebrand", "campaign-retrospective". These are added alongside auto-detected tags, not replacing them
- **Exclude patterns (optional)**: Content patterns or types to skip during this sync — e.g., exclude draft insights, partial campaign data, or specific content types. Prevents syncing incomplete or work-in-progress knowledge

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Load sync state**: Run `memory-manager.py --action sync-insights` to load the last sync checkpoint from `~/.claude-marketing/brands/{slug}/memory/sync-state.json`. Identify the last sync timestamp, items previously synced (by content hash), and any partial sync that needs resuming from its failure point. If force sync is requested, reset the checkpoint to epoch zero.
3. **Gather syncable items**: Load insights.json entries, campaign data from `campaigns/`, and session learnings accumulated in the current working context. Apply sync scope filter (all, insights-only, campaigns-only) and exclude patterns to build the candidate set.
4. **Identify new and modified items**: Diff the candidate set against the sync checkpoint. Generate content hashes (SHA-256) for each candidate and compare against the local content hash registry. Separate items into: new (not previously synced), modified (content changed since last sync — hash mismatch), and unchanged (already synced — skip). Report the diff summary before proceeding.
5. **Prepare storage payloads**: For each new or modified item, run `memory-manager.py --action prepare-store` to structure the metadata payload — auto-detect content_type based on source (insight entries become `performance-insight`, campaign retrospectives become `campaign-learning`, strategy decisions become `campaign-learning`, guidelines become `guideline`), apply auto-detected tags plus any user-specified batch tags, and set source to `sync`.
6. **Check connected memory services**: Run `memory-manager.py --action get-memory-status` to verify which vector database is available and confirm it has capacity for the sync batch. Report estimated storage impact (items to add, storage utilization after sync). If no persistent storage is connected, store locally and recommend setup.
7. **Execute batch storage**: Store each prepared item via the connected Pinecone or Qdrant MCP. Process items sequentially to handle failures gracefully — if one item fails, log the failure with error details and continue with the remaining items. For each successful storage, update the local content hash registry immediately so progress is not lost if the sync is interrupted.
8. **Update sync state**: After all items are processed, update `sync-state.json` with the new checkpoint timestamp, cumulative items synced, items skipped, items failed (with content hashes for retry), and per-layer storage status. If any items failed, their hashes are queued for automatic retry on the next sync run.
9. **Report sync summary**: Present the complete sync report with actionable details — what was synced, what was skipped and why, what failed and how to fix it, storage utilization status, and the current state of persistent memory for this brand.

## Output

A structured sync report containing:

- **Sync summary**: Total items processed with breakdown — new items synced, modified items updated, duplicates skipped (with count by reason: hash match, exclude pattern), and items failed with specific error reasons and remediation steps per failure
- **Items synced detail**: List of each synced item with content summary (first 100 characters), content_type assigned, tags applied (auto-detected + batch tags), and storage ID in the vector database for reference
- **Items skipped**: Duplicates and excluded items listed with reason — content hash match (already in persistent storage), exclude pattern hit, or unchanged since last sync — so the user can verify nothing important was missed
- **Items failed**: Any items that could not be stored — with full error message, failure reason (API timeout, validation error, capacity limit, malformed payload), content hash for retry identification, and specific remediation steps
- **Sync state update**: New checkpoint timestamp, cumulative items in persistent memory (total across all syncs), delta since last sync (net new items), and estimated next sync size based on current session activity rate
- **Per-layer status**: Which memory layers received data — vector DB items stored (with namespace), knowledge graph entities created (if Graphiti connected), cross-session entries updated (if Supermemory connected), and local index entries registered
- **Storage capacity**: Current utilization of the connected vector database — total items stored, estimated capacity remaining, utilization percentage, and alert if approaching provider plan limits
- **Next sync recommendation**: Suggested timing for next sync based on session activity volume and storage capacity — with a reminder that running `/digital-marketing-pro:sync-memory` before ending a session ensures no learnings are lost

## Agents Used

- **memory-manager** — Sync checkpoint loading and incremental diff calculation against content hash registry, SHA-256 hash generation for new and modified item detection, payload preparation with auto-classified content types and source-based tagging, batch storage execution via vector database MCP with per-item error handling and progress persistence, local index and content hash registry updates after each successful store, sync state checkpoint management with partial-progress recovery for interrupted syncs, storage capacity monitoring with utilization alerts, and comprehensive sync report generation with retry queue management
