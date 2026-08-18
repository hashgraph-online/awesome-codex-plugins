# Schema Introspection & Robot-Mode Contracts

> **One-liner:** cass is **fully self-describing**. Every command, flag, response, and error code is queryable at runtime. Use this when the skill or your memory is uncertain.

## Contents

- [The Discovery Trinity](#the-discovery-trinity)
- [introspect Schema](#introspect-schema)
- [capabilities Schema](#capabilities-schema)
- [Robot Output Conventions](#robot-output-conventions)
- [Robot-Format Output Modes](#robot-format-output-modes)
- [Response `_meta` Fields](#response-_meta-fields)
- [Agent Self-Configuration Pattern](#agent-self-configuration-pattern)

---

## The Discovery Trinity

```bash
cass --robot-help                  # Top-level machine help
cass robot-docs <topic>            # Topic-scoped docs
cass introspect --json             # Full schema dump (commands + responses)
cass capabilities --json           # Static features + limits
```

### `robot-docs` Topics

```
guide       — Quickstart for automation
commands    — Every subcommand + arg
examples    — Copy-paste workflows
schemas     — Auto-generated response schemas
contracts   — Output stream conventions (stdout=data, stderr=diag)
```

If a topic returns "Could not parse arguments", that topic is unsupported in your installed cass version.

---

## introspect Schema

```bash
cass introspect --json | jq '{
  api_version,
  contract_version,
  commands: .commands | map(.name),
  responses: .response_schemas | keys
}'
```

Returns:
- `commands[]` — every command with `name`, `description`, `arguments[]`, `has_json_output`
- `arguments[]` per command — `name`, `description`, `arg_type` (flag/option), `value_type`, `required`, `default`, `enum_values`, `repeatable`
- `response_schemas` — declared field shapes for every JSON-emitting command
- `global_flags` — top-level flags valid for all subcommands

This is the source of truth — newer than any handwritten skill.

### Programmatic Discovery

```bash
# What commands have a JSON response?
cass introspect --json | jq '.commands[] | select(.has_json_output) | .name'

# Find commands that accept --workspace
cass introspect --json | jq '.commands[] | select(.arguments[]?.name == "workspace") | .name'

# What enum values does --mode accept?
cass introspect --json \
  | jq '.commands[] | select(.name == "search") | .arguments[] | select(.name == "mode") | .enum_values'
```

---

## capabilities Schema

```json
{
  "crate_version": "0.3.6",
  "api_version": 1,
  "contract_version": "1",
  "features": [
    "json_output", "jsonl_output", "robot_meta", "time_filters",
    "field_selection", "content_truncation", "aggregations",
    "wildcard_fallback", "timeout", "cursor_pagination",
    "request_id", "dry_run", "query_explain", "view_command",
    "status_command", "state_command", "api_version_command",
    "introspect_command", "export_command", "expand_command",
    "timeline_command", "highlight_matches"
  ],
  "connectors": [...],
  "limits": {
    "max_limit": 0,
    "max_content_length": 0,
    "max_fields": 50,
    "max_agg_buckets": 10
  }
}
```

`max_limit: 0` means **no enforced cap** (RAM-clamped at runtime). `max_*: 0` consistently means "uncapped".

### Version-Aware Patterns

`features[]` enumerates capabilities; output formats are NOT in `features[]` — they live in each subcommand's per-arg enum. `--robot-format` is **per-subcommand, not global** (`global_flags` only contains `db`, `robot-help`, `trace-file`, `quiet`, `verbose`, `color`, `progress`, `wrap`, `nowrap`).

```bash
# Probe a feature (real entry in features[])
HAS_AGG=$(cass capabilities --json | jq -r '.features | index("aggregations") != null')

# Probe a robot-format value for `cass search` specifically
cass introspect --json \
  | jq -r '.commands[]
            | select(.name=="search")
            | .arguments[]
            | select(.name=="robot-format")
            | .enum_values[]'
# json jsonl compact sessions toon
```

---

## Robot Output Conventions

```
stdout = data only (parseable by --json)
stderr = diagnostics, progress events, warnings
exit 0 = success
exit 1 = recoverable error (retry with different args)
exit 2 = invalid args / contract violation
```

Always `2>/dev/null` when you need clean JSON on stdout, **unless** you're consuming progress events from stderr (during indexing).

---

## Robot-Format Output Modes

```bash
--robot-format json       # default; pretty-printed
--robot-format jsonl      # one event per line; streams big result sets
--robot-format compact    # single-line JSON; smallest token cost
--robot-format sessions   # one source_path per line; pipe into `cass search --sessions-from -`
--robot-format toon       # token-optimized object notation (saves ~30% vs JSON)
```

### Chained Searches via `sessions` format

```bash
# Step 1: get sessions matching a coarse filter
cass search "auth" --workspace /repo --robot-format sessions > /tmp/auth-sessions.txt

# Step 2: search within only those sessions
cass search "JWT" --sessions-from /tmp/auth-sessions.txt --json --fields minimal

# Or pipe directly:
cass search "auth" --robot-format sessions | cass search "JWT" --sessions-from -
```

Two-pass is a 10x speedup vs one big query when your filter is narrow.

---

## Response `_meta` Fields

When you pass `--robot-meta`, every search response gets:

```json
"_meta": {
  "elapsed_ms": 42,
  "wildcard_fallback": false,
  "cache_stats": {"hits": 12, "misses": 3, "shortfall": 0},
  "tokens_estimated": 850,
  "max_tokens": 1200,
  "next_cursor": "eyJ...",
  "hits_clamped": false,
  "fallback_mode": null,           // "lexical" if --mode hybrid degraded
  "index_freshness": {
    "fresh": true,
    "age_seconds": 122,
    "stale": false,
    "last_indexed_at": "2026-04-22T19:45:06Z",
    "pending_sessions": 0
  },
  "state": {"index": "...", "database": "..."},
  "request_id": "run-1"
}
```

`_warning` (top-level) is set when the index is stale enough to cast doubt on results. Always check it; surface to the user verbatim.

---

## Agent Self-Configuration Pattern

Use introspection to auto-tune behavior to whatever cass version is installed:

```bash
caps=$(cass capabilities --json)
intro=$(cass introspect --json)

VERSION=$(jq -r '.crate_version' <<< "$caps")
HAS_HYBRID=$(jq -r '.features | index("hybrid_search") != null' <<< "$caps")
SEARCH_FIELDS=$(jq -r '.commands[] | select(.name=="search") | .arguments[] | select(.name=="fields") | .description' <<< "$intro")

echo "Running cass $VERSION; hybrid=$HAS_HYBRID; fields-help=$SEARCH_FIELDS"
```

This way a single skill file works across cass versions — the agent adapts.
