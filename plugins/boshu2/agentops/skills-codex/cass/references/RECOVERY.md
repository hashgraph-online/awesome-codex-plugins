# Doctor & Bounded Authorized Recovery

> **The contract:** Select recovery only when needed and authorized for its sources, model, destination and derived-state writes. Healthy and stale-but-usable indexes can be searched immediately. A search-only request does not authorize refresh/rebuild; unknown status is not proof of corruption. Preserve source sessions and bound recovery commands with a wall-clock cap.

## Contents

- [When to Run Each Doctor Mode](#when-to-run-each-doctor-mode)
- [Output Schema (top-level keys, no `.summary` wrapper)](#output-schema-top-level-keys-no-summary-wrapper)
- [Real-World Recovery Recipes](#real-world-recovery-recipes)
- [What `--fix` Does NOT Do](#what---fix-does-not-do)
- [Disk Cleanup (ALWAYS ask first)](#disk-cleanup-always-ask-first)
- [Optional Recovery Invocation](#optional-recovery-invocation)

---

## When to Run Each Doctor Mode

```bash
cass doctor --json                       # Read-only diagnosis
cass doctor --json --verbose             # Show passed checks too
timeout 600 cass doctor --fix --json     # Apply selected authorized repairs
timeout 600 cass doctor --fix --force-rebuild --json # Force only for a diagnosed need
```

`--fix` runs a 7-step protocol:

1. **Data directory** — Create if missing
2. **Stale lock files** — Remove `.index.lock` if older than 1h
3. **Database open + quick_check** — Backup to `.corrupt.<ts>` and rebuild if quick_check fails
4. **FTS table** — Verify `fts_messages` is queryable via frankensqlite
5. **Tantivy index** — Rebuild from SQLite if empty/missing/stale
6. **Config files** — Validate `config.toml` and `sources.toml` parse
7. **Session directories** — Detect `~/.claude`, `~/.codex`, etc. for visibility

Backup format: `agent_search.db.corrupt.20260315_154822_759` (sortable timestamp). Corruption salvage is preserved for forensic review.

---

## Output Schema (top-level keys, no `.summary` wrapper)

```json
{
  "status": "healthy|unhealthy",
  "healthy": true,
  "initialized": true,
  "explanation": null,
  "recommended_action": null,
  "needs_rebuild": false,
  "issues_found": 0,
  "issues_fixed": 0,
  "warnings": [],
  "failures": [],
  "auto_fix_applied": false,
  "auto_fix_actions": [],
  "checks": [
    {"name": "database", "status": "pass|warn|fail",
     "message": "...", "fix_available": true, "fix_applied": false},
    ...
  ],
  "_meta": {...}
}
```

Parse `failures[]` (top-level array of failed check names) for blocking issues. Anything in `auto_fix_actions` happened automatically. **Do not look for a `.summary` key — it doesn't exist.**

```bash
timeout 600 cass doctor --fix --json | jq '{
  ok: .healthy,
  issues_found, issues_fixed,
  applied: .auto_fix_actions,
  failed: [.checks[] | select(.status=="fail") | .name]
}'
```

---

## Real-World Recovery Recipes

### Index empty but DB has rows

```bash
# Symptom
cass status --json | jq '.database.messages, .index.documents'
# 664027  0

# Fix
timeout 600 cass doctor --fix --json | jq '.auto_fix_actions'
# ["Rebuilt search index from database"]
```

### Database file unreadable

```bash
# Symptom: cass status returns counts_skipped=true and open_error
cass status --json | jq '.database.open_error'
# "database disk image is malformed"

# Fix
timeout 600 cass doctor --fix --json
# Backs up bad DB to .corrupt.<ts>, then rebuilds index from corrupt-salvage if possible
```

### Stale lock from crashed indexer

```bash
# Symptom: "Index rebuild is already in progress" but no cass process exists
ps -p $(cass status --json | jq -r '.active_index.pid // empty')
# (no such process)

# Fix (doctor handles >1h-old locks; for fresher locks, force it)
timeout 600 cass doctor --fix --force-rebuild --json
```

### Incremental index hangs at current:0 (OPEN issue #196)

```bash
# Workaround until fixed upstream
pkill -f "cass index"
timeout 600 cass index --full --force-rebuild --json
```

`cass status` keeps showing `rebuilding` after the kill? `cass doctor --fix` clears the run lock.

### Full rebuild "succeeds" then fails on `last_indexed_at` write (FIXED at HEAD as of 2026-04-22)

**Status:** Fixed by commit `e06342f2` (bead `coding_agent_session_search-zz8ni`, closed). Affects **v0.3.6 and earlier**. Once you're on a build that includes the fix, the rebuild reports `{"success": true}` and the missing-marker case logs a deferred-update warning instead of bubbling out as failure. The recovery recipe below remains valid as a workaround for older binaries.



**Symptom:** `cass index --full --force-rebuild --json` runs for 3–5 minutes processing all 51k+ docs, then exits with:

```json
{"success": false,
 "error": "index failed: updating last_indexed_at after index run ... database is busy",
 "code": 9, "kind": "index", "retryable": true}
```

**Diagnosis:** The index *data* committed successfully. Only `persist_final_index_run_metadata` (src/indexer/mod.rs:6295) lost the writer race against a concurrent cass process. `cass status` keeps reporting "stale" because the freshness marker never landed.

**Verify the index is actually good:**

```bash
cass search "common-term-from-your-corpus" --limit 1 --json --robot-meta \
  | jq '{total: .total_matches, fresh_at_query_time: ._meta.index_freshness.fresh}'
# total > 0 means the data is committed and queryable
```

**Fix without re-running the 5-minute rebuild:**

```bash
# Wait for any concurrent cass processes to settle
sleep 30
# A trivial incremental run is usually enough to land the timestamp
timeout 600 cass index --json
```

If a concurrent rebuild is still active (`cass status --json | jq '.rebuild.active'`), the timestamp will be written when it completes. Don't fight it.

**Root cause** (for future fixers): the `with_concurrent_retry` wrapper at line 6302 uses `begin_concurrent_retry_limit()` retries — under sustained contention from peer cass processes, all retries exhaust and the metadata write fails *after* the index data has already been committed. A graceful path would log a warning and return Ok rather than discarding the whole run's success.

---

## What `--fix` Does NOT Do

- **Delete source session files** (`~/.claude/projects/*.jsonl` etc.) — these are user data, never touched
- **Delete corrupt DB backups** — preserved as `.corrupt.<ts>` and `.salvage-<ts>.{sql,sqlite3}`
- **Modify `sources.toml`** — config changes require explicit `cass sources` commands
- **Re-download semantic models** — that requires `cass models install`
- **Cross network boundaries** — only operates on local data dir

When recovery is already authorized, run the selected bounded repair and report the result without asking again. Source preservation alone does not grant recovery scope or permission to read additional sources.

---

## Disk Cleanup (ALWAYS ask first)

The cass project dir can accumulate large artifacts after crashes:

```bash
# Surface what's eating disk; do not delete anything yourself
du -sh ~/.local/share/coding-agent-search/* | sort -hr
# Plus historical core dumps in /dp/coding_agent_session_search/core.NNNNN
```

Per the project rule **"NEVER delete a file without express permission"** (AGENTS.md), every deletion below requires explicit user approval — even backups you suspect are stale:

| File pattern | Why kept | Ask before deleting |
|--------------|----------|---------------------|
| `*.corrupt.<ts>` | Salvage source for past corruption | Yes |
| `*.salvage-<ts>.{sql,sqlite3}` | Forensic snapshot | Yes |
| `core.NNNNN` (multi-GB) | Debugging crashes | Yes |
| `agent_search.db.bak-*` | Manual backups | Yes |
| `agent_search.db` (active) | Live data | Always (and almost never) |

Surface the disk usage, list candidates with sizes/ages, and let the user decide. They have the context for what's safe.

---

## Optional Recovery Invocation

Do not install a search hook or start an index watcher as part of retrieval.
When recovery is needed and its full derived-state scope is already authorized,
inspect and invoke the existing helper:

```bash
# This may refresh a stale index or repair/rebuild derived state.
CASS_STATUS_TIMEOUT=15 CASS_REBUILD_TIMEOUT=600 ./scripts/recover.sh
```

The helper's individual index calls are capped. A stale usable index is still
searchable; refreshing is an optional selected operation, not a prerequisite.
If a status read is unavailable or an existing rebuild is progressing, retain
that uncertainty rather than stacking another repair. See
[OBSERVABILITY.md](OBSERVABILITY.md#authoritative-fallback-and-concurrent-read-latency).
