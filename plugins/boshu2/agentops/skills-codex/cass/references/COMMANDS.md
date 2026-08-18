# cass Command Reference

> **Freedom Key:** LOW = exact syntax required | MEDIUM = some flexibility | HIGH = multiple approaches

## Contents

- [Lifecycle Commands [LOW freedom]](#lifecycle-commands-low-freedom)
- [Search Command [MEDIUM freedom]](#search-command-medium-freedom)
- [View & Expand [LOW freedom]](#view--expand-low-freedom)
- [Export [LOW freedom]](#export-low-freedom)
- [Context [MEDIUM freedom]](#context-medium-freedom)
- [Timeline [MEDIUM freedom]](#timeline-medium-freedom)
- [Pagination [LOW freedom]](#pagination-low-freedom)
- [Chained Searches [MEDIUM freedom]](#chained-searches-medium-freedom)
- [Output Schemas](#output-schemas)
- [Exit Codes](#exit-codes)

---

## Lifecycle Commands [LOW freedom]

```bash
cass status --json              # Health check — is index current?
cass index --json               # Incremental refresh (fast, use first)
cass index --full --json        # Full rebuild (when stale)
cass capabilities --json        # What this install supports
cass diag --json                # Detailed diagnostics
cass doctor                     # Repair (safe, won't delete sources)
```

### Status Output

```json
{
  "database": {"conversations": 4827, "messages": 664027},
  "index": {"fresh": true, "stale": false},
  "recommended_action": "Index is up to date"
}
```

---

## Search Command [MEDIUM freedom]

### Basic Form

```bash
cass search "QUERY" --workspace /path --json --fields minimal --limit N
```

**Every search needs:** `--json`, `--fields minimal`, `--limit N` (N > 0)

### Filtering

| Filter | Example |
|--------|---------|
| By workspace | `--workspace /data/projects/foo` |
| By agent | `--agent claude_code` |
| By mode | `--mode lexical` (default), `semantic`, `hybrid` |
| From session list | `--sessions-from /tmp/sessions.txt` |

### Output Control

| Flag | Effect | Token Impact |
|------|--------|--------------|
| `--fields minimal` | source_path, line_number, agent | **5x smaller** |
| `--fields summary` | + title, score | 2x smaller |
| `--max-content-length N` | Truncate snippets | Reduces size |
| `--max-tokens N` | Soft token budget | Caps output |

### Aggregations [LOW freedom]

```bash
cass search "*" --workspace /path --aggregate agent,date --limit 1 --json
```

**MUST use `--limit 1`** (not 0). Ignore `.hits`, parse `.aggregations` only.

```json
{
  "aggregations": {
    "agent": {"buckets": [{"key": "claude_code", "count": 925}]},
    "date": {"buckets": [{"key": "2026-01-16", "count": 112}]}
  }
}
```

Available: `agent`, `date`, `workspace`

### Robot Formats

| Flag | Output | Use Case |
|------|--------|----------|
| `--robot-format sessions` | Session paths only | Chaining searches |
| `--robot-format jsonl` | Streaming NDJSON | Large result sets |
| `--robot-meta` | Include `_meta` block | Check freshness |

### Debug

```bash
cass search "QUERY" --workspace /path --dry-run --explain
```

---

## View & Expand [LOW freedom]

### View (Line-Oriented)

```bash
cass view /path/to/session.jsonl -n LINE -C CONTEXT
```

| Flag | Meaning |
|------|---------|
| `-n LINE` | Center on this line |
| `-C N` | N lines before AND after |
| `-A N` | N lines after only |
| `-B N` | N lines before only |

### Expand (Message-Oriented)

```bash
cass expand /path/to/session.jsonl --line LINE --context N
```

**Use `expand` for conversation flow, `view` for raw debugging.**

---

## Export [LOW freedom]

```bash
cass export /path.jsonl --format json --include-tools -o /tmp/output.json
```

**CRITICAL:** Always export to file first. Piping causes broken pipe panic.

```bash
# WRONG (may panic):
cass export /path.jsonl --format json | head -100

# RIGHT:
cass export /path.jsonl --format json -o /tmp/out.json
jq '.[0:100]' /tmp/out.json
```

| Flag | Effect |
|------|--------|
| `--format json` | Machine parsing |
| `--format markdown` | Human review |
| `--include-tools` | Include tool calls (hidden by default) |
| `-o FILE` | Output file (required) |

---

## Context [MEDIUM freedom]

```bash
cass context /path/to/session.jsonl --json
```

Finds related sessions: same workspace, same day, same agent.

```json
{
  "related_sessions": [...],
  "same_workspace": 12,
  "same_day": 8,
  "same_agent": 15
}
```

---

## Timeline [MEDIUM freedom]

```bash
cass timeline --since 2026-01-14 --until 2026-01-17 --workspace /path --json
cass timeline --since 7d --json
```

**Prefer aggregations** — more predictable JSON:
```bash
cass search "*" --workspace /path --aggregate date --limit 1 --json
```

---

## Pagination [LOW freedom]

```bash
# First page
cass search "KEYWORD" --json --robot-meta --limit 50 --request-id run-1

# Next page (use _meta.next_cursor)
cass search "KEYWORD" --json --robot-meta --limit 50 --cursor "eyJ..." --request-id run-1b
```

---

## Chained Searches [MEDIUM freedom]

```bash
# Step 1: Get sessions matching coarse filter
cass search "COARSE" --workspace /path --robot-format sessions > /tmp/sessions.txt

# Step 2: Search within only those
cass search "SPECIFIC" --sessions-from /tmp/sessions.txt --json --fields minimal

# Or via pipe:
cass search "COARSE" --robot-format sessions | cass search "SPECIFIC" --sessions-from -
```

---

## Output Schemas

### Search Response

```json
{
  "hits": [
    {
      "source_path": "/path/to/session.jsonl",
      "line_number": 42,
      "agent": "claude_code",
      "title": "First few words...",
      "score": 15.234,
      "created_at": "2026-01-16T10:30:00Z"
    }
  ],
  "total_matches": 125,
  "aggregations": {...}
}
```

### Field Presets

| Preset | Fields |
|--------|--------|
| `minimal` | source_path, line_number, agent |
| `summary` | source_path, line_number, agent, title, score |
| `full` | All fields including content |

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | Success | Continue |
| `1` | Error (index, query) | Check `cass status`, re-index |
| `2` | Invalid args, special chars | Quote query, simplify |
