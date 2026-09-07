# Health, Status, and Index Freshness

> **One-liner:** cass exposes three overlapping health surfaces. Knowing which to use prevents the #1 mistake (treating "stale" as "broken").

## Contents

- [The Four Commands](#the-four-commands)
- [Status Schema (the one you'll actually parse)](#status-schema-the-one-youll-actually-parse)
- [The Three States, Read Off Status](#the-three-states-read-off-status)
- [NDJSON Progress on stderr](#ndjson-progress-on-stderr)
- [Authoritative Fallback and Concurrent Read Latency](#authoritative-fallback-and-concurrent-read-latency)
- [Liveness Stack](#liveness-stack)
- [Capabilities Self-Check](#capabilities-self-check)

---

## The Four Commands

| Command | Latency | Output | Best For |
|---------|---------|--------|----------|
| `cass health` | <50ms | Exit code 0/1 | Pre-flight gating in hooks/cron |
| `cass status --json` | ~100-700ms | Full JSON | Branching agent logic |
| `cass diag --json` | ~500ms-2s | Path/size diagnostics | Bug reports, deep triage |
| `cass capabilities --json` | <10ms | Static feature list | Version-aware fallbacks |

`status` and `state` are aliases for the same command.

---

## Status Schema (the one you'll actually parse)

```json
{
  "status": "healthy|unhealthy|rebuilding|initializing",
  "healthy": true,
  "initialized": true,
  "explanation": "...",            // null when healthy
  "recommended_action": "...",     // null when nothing to do

  "index": {
    "exists": true,
    "status": "fresh|stale|missing|rebuilding",
    "fresh": true,
    "stale": false,
    "age_seconds": 1234,
    "stale_threshold_seconds": 1800,
    "rebuilding": false,
    "documents": 51214,
    "fingerprint": {
      "current_db_fingerprint": "content-v1:51214:51214:4711459",
      "checkpoint_fingerprint": "content-v1:51214:51214:4711459",
      "matches_current_db_fingerprint": true
    },
    "checkpoint": {
      "present": true,
      "completed": true,
      "db_matches": true,
      "schema_matches": true,
      "page_size_compatible": true
    }
  },

  "database": {
    "exists": true,
    "opened": true,
    "conversations": 4827,
    "messages": 664027,
    "open_error": null,
    "open_retryable": false,
    "counts_skipped": false
  },

  "pending": {
    "sessions": 0,
    "watch_active": true,
    "orphaned": false
  },

  "rebuild": {
    "active": true,
    "orphaned": false,
    "pid": 3472773,
    "mode": "incremental",
    "job_id": "lexical_refresh-...",
    "job_kind": "lexical_refresh",
    "phase": "indexing",
    "started_at": "2026-04-22T20:18:45Z",
    "updated_at": "2026-04-22T20:21:09Z",
    "processed_conversations": 12,
    "total_conversations": 145,
    "indexed_docs": 410
  },

  "semantic": {
    "status": "missing|partial|installed",
    "available": false,
    "can_search": false,
    "fallback_mode": "lexical",
    "preferred_backend": "fastembed",
    "embedder_id": "minilm-384",
    "hint": "Run 'cass models install'..."
  },

  // active_index appears ONLY while a rebuild is running.
  // For the always-present pid/phase, read .rebuild instead.
  "active_index": {
    "pid": 3472773,
    "data_dir": "/home/.../coding-agent-search",
    "db_path": "/home/.../agent_search.db",
    "started_at": "2026-04-22T20:18:45.804+00:00",
    "job_id": "lexical_refresh-...",
    "job_kind": "lexical_refresh",
    "phase": "index"
  }
}
```

---

## The Three States, Read Off Status

```bash
# Fresh & ready
.healthy=true && .index.fresh=true

# Stale-but-usable (most common — DON'T panic)
.healthy=false && .index.stale=true && .database.exists=true && .database.messages > 0

# Truly broken
.database.exists=false  # never indexed
   OR .database.open_error != null
   OR .index.documents=0 && .database.messages > 0
   OR .index.fingerprint.matches_current_db_fingerprint=false
```

### Decision Function (Bash)

```bash
cass_classify() {
  local s=$(cass status --json)
  local fresh=$(echo "$s" | jq -r '.index.fresh')
  local db_exists=$(echo "$s" | jq -r '.database.exists')
  local docs=$(echo "$s" | jq -r '.index.documents // 0')
  local msgs=$(echo "$s" | jq -r '.database.messages // 0')

  if [ "$fresh" = "true" ]; then
    echo "READY"
  elif [ "$db_exists" = "true" ] && [ "$msgs" != "0" ] && [ "$docs" != "0" ]; then
    echo "STALE_BUT_USABLE"
  else
    echo "BROKEN"
  fi
}
```

---

## NDJSON Progress on stderr

When you run `cass index --json`, **stderr** streams progress events:

```
{"event":"started","mode":"incremental","full":false}
{"event":"phase","phase":"preparing","elapsed_ms":6000}
{"event":"phase","phase":"indexing","total":145,"current":12,"elapsed_ms":12000,"rate_per_sec":1.0,"eta_seconds":133}
{"event":"completed","conversations":145,"elapsed_ms":25000}
```

Tune the cadence: `--progress-interval-ms 1000` (clamped 250–60000). Disable: `--no-progress-events` or `CASS_INDEX_NO_PROGRESS_EVENTS=1`.

**This is how you detect issue #196 (stuck indexing):** if `current` doesn't advance for >30s of progress events, kill and retry with `--full --force-rebuild`.

## Authoritative Fallback and Concurrent Read Latency

`cass index --json` names the requested mode, not a guarantee that every source
can be reconciled incrementally. The indexer may discover an incompatible or
incomplete derived checkpoint and expand into an authoritative rebuild across
the full conversation corpus. A suddenly large `.rebuild.total_conversations`
therefore describes the chosen recovery work; by itself it says nothing about
loss of the source session files.

The active writer can also make concurrent `status` and `search` calls slower
than the normal latency table above. Keep observations bounded and preserve the
difference between timeout, command failure, and an actual empty result:

```bash
status_rc=0
timeout 15 cass status --json > /tmp/cass-status.json || status_rc=$?
search_rc=0
timeout 30 cass search "QUERY" --json --fields minimal --limit 20 \
  > /tmp/cass-search.json || search_rc=$?

case "$status_rc" in
  0) jq '{index, rebuild}' /tmp/cass-status.json ;;
  124) echo 'status not observed within 15s' ;;
  *) echo "status failed with exit $status_rc" ;;
esac

case "$search_rc" in
  0) jq '{total_matches, hits}' /tmp/cass-search.json ;;
  124) echo 'search not observed within 30s (not a zero-hit result)' ;;
  *) echo "search failed with exit $search_rc" ;;
esac
```

When status succeeds, compare `.rebuild.updated_at` and
`.rebuild.processed_conversations` across bounded observations. Movement means
the authoritative run is progressing; let that single writer converge. If the
values do not move, follow the existing issue #196 recovery guidance. Never use
a timed-out read, a large rebuild total, or a temporary `rebuilding` state as a
claim that data was lost.

---

## Liveness Stack

Layer 1 — The Trinity:
```bash
cass health --json     # 50ms, exit-code only
cass status --json     # ~500ms, structured JSON
cass diag --json       # ~1-2s, paths/sizes/disk
```

Layer 2 — The Process:
```bash
# .rebuild is always present (active=false when idle); .active_index appears only during a run
cass status --json | jq '{rebuild, active_index: (.active_index // null)}'
PID=$(cass status --json | jq -r '.rebuild.pid // empty')
[ -n "$PID" ] && ps -p "$PID" || echo "no rebuild running"
```

Layer 3 — Observability hooks:
```bash
cass --trace-file /tmp/cass-trace.jsonl search "X" --json   # span timing
```

---

## Capabilities Self-Check

Before issuing a flag your agent isn't sure exists, gate on `capabilities`:

```bash
HAS_HYBRID=$(cass capabilities --json | jq -r '.features | index("hybrid_search") != null')
if [ "$HAS_HYBRID" = "true" ]; then
  cass search "X" --mode hybrid --json
else
  cass search "X" --json   # fall back to lexical
fi
```

`features[]` enumerates: `json_output, jsonl_output, robot_meta, time_filters, field_selection, content_truncation, aggregations, wildcard_fallback, timeout, cursor_pagination, request_id, dry_run, query_explain, view_command, status_command, state_command, api_version_command, introspect_command, export_command, expand_command, timeline_command, highlight_matches, ...`.

Limits live in `limits{max_limit, max_content_length, max_fields, max_agg_buckets}`. `max_limit=0` means "no enforced cap" (clamped at runtime by RAM).
