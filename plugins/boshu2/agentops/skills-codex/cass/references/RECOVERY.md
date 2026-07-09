# Doctor & Autonomous Recovery

> **The contract:** `cass doctor --fix --json` is **safe by default**. It rebuilds derived data (Tantivy index, FTS table) from source SQLite — it never deletes source session files. Use it without asking the user.

## Contents

- [When to Run Each Doctor Mode](#when-to-run-each-doctor-mode)
- [Output Schema (top-level keys, no `.summary` wrapper)](#output-schema-top-level-keys-no-summary-wrapper)
- [Real-World Recovery Recipes](#real-world-recovery-recipes)
- [What `--fix` Does NOT Do](#what---fix-does-not-do)
- [Disk Cleanup (ALWAYS ask first)](#disk-cleanup-always-ask-first)
- [Pre-Flight Hook Pattern](#pre-flight-hook-pattern)

---

## When to Run Each Doctor Mode

```bash
cass doctor --json                       # Read-only diagnosis
cass doctor --json --verbose             # Show passed checks too
cass doctor --fix --json                 # Apply safe rebuilds (USE THIS)
cass doctor --fix --force-rebuild --json # Same + force index rebuild even if healthy
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
cass doctor --fix --json | jq '{
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
cass doctor --fix --json | jq '.summary.auto_fix_actions'
# ["Rebuilt search index from database"]
```

### Database file unreadable

```bash
# Symptom: cass status returns counts_skipped=true and open_error
cass status --json | jq '.database.open_error'
# "database disk image is malformed"

# Fix
cass doctor --fix --json
# Backs up bad DB to .corrupt.<ts>, then rebuilds index from corrupt-salvage if possible
```

### Stale lock from crashed indexer

```bash
# Symptom: "Index rebuild is already in progress" but no cass process exists
ps -p $(cass status --json | jq -r '.active_index.pid // empty')
# (no such process)

# Fix (doctor handles >1h-old locks; for fresher locks, force it)
cass doctor --fix --force-rebuild --json
```

### Incremental index hangs at current:0 (OPEN issue #196)

```bash
# Workaround until fixed upstream
pkill -f "cass index"
cass index --full --force-rebuild --json
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
cass index --json
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

So you can run `cass doctor --fix` autonomously without permission. Document the action in your response, but don't ask first.

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

## Pre-Flight Hook Pattern

For agents that should never run against a broken index:

```bash
#!/usr/bin/env bash
# pre-cass-search.sh
# Decision tree: fresh → ok, stale-but-usable → bg refresh + ok, broken → doctor
set -uo pipefail

# 50ms preflight: exit 0 means already-fresh
if cass health --json >/dev/null 2>&1; then
  exit 0
fi

# Health failed — read full status to differentiate stale vs broken
state=$(cass status --json 2>/dev/null \
  | jq -r '"\(.index.stale // false),\(.database.exists // false),\(.database.messages // 0),\(.index.documents // 0)"')

case "$state" in
  true,true,*)
    # stale index, DB present — usable; refresh in background
    cass index --json >/tmp/cass-bg.log 2>&1 &
    disown || true
    exit 0
    ;;
  *)
    # broken / uninitialized / DB missing — try to repair (doctor never deletes sources)
    if cass doctor --fix --json >&2; then
      cass health --json >/dev/null 2>&1 && exit 0 || exit 1
    else
      exit 1
    fi
    ;;
esac
```

Wire into Claude Code as a `PreToolUse` hook scoped to `cass search`. Use the same shape as `scripts/recover.sh` for the inline decision tree.
