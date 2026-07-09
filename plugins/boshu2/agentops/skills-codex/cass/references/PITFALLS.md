# cass Pitfalls & Troubleshooting

> **Quick lookup:** Ctrl+F for your error message or symptom.

## Contents

- [Quick Diagnosis](#quick-diagnosis)
- [Index Problems](#index-problems)
- [Query Errors](#query-errors)
- [Output Problems](#output-problems)
- [Content Not Found](#content-not-found)
- [jq Problems](#jq-problems)
- [Diagnostic Workflow](#diagnostic-workflow)
- [Exit Codes](#exit-codes)
- [Pro Tips](#pro-tips)

---

## Quick Diagnosis

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 0 results but content exists | Workspace path mismatch | Use `--aggregate workspace` to find exact path |
| `--limit 0` panic | Invalid limit | Always use `--limit 1` minimum |
| Exit code 2 | Special characters in query | Quote query or use nearby anchor |
| Broken pipe on export | Piping large output | Export to file first with `-o` |
| Tool calls hidden | Missing flag | Add `--include-tools` to export |
| Stale results | Index needs refresh | Run `cass index --json` |
| jq returns null | Wrong field name | Use `jq 'keys'` to check structure |
| Can see in file, cass finds nothing | Content not indexed | Fallback to `rg` on raw file |

---

## Index Problems

### "Index is stale" / Missing Recent Sessions

```bash
cass status --json              # Check state
cass index --json               # Incremental refresh (try first)
cass index --full --json        # Full rebuild (if still stale)
```

### Index Shows 0 Conversations

```bash
# Find session files
find ~/.claude/projects -name "*.jsonl" | head -5

# Full rebuild
cass index --full --json

# Check capabilities
cass capabilities --json
```

### Database Corruption

```bash
cass doctor    # Safe repair — won't delete source sessions
cass index --full --json
```

---

## Query Errors

### `--limit 0` Panic

```bash
# WRONG:
cass search "*" --workspace /path --aggregate agent --limit 0 --json

# RIGHT:
cass search "*" --workspace /path --aggregate agent --limit 1 --json
```

### Workspace Path Mismatch (0 Results)

Paths must match exactly — case-sensitive, no trailing slash.

```bash
# Discover exact path:
cass search "your_keyword" --aggregate workspace --json
```

### Special Characters Fail

**Problem chars:** `--`, `|`, `"`, `'`, `*`, `?`, `\`

```bash
# Quote the term
cass search '"--fields"' --workspace /path --json

# Use nearby anchor without special chars
cass search "fields minimal" --workspace /path --json

# Escape in double-quotes
cass search "\"role\":\"user\"" --workspace /path --json
```

### Query With Leading Dashes Fails

```bash
# Wrap in quotes
cass search '"--workspace"' --workspace /path --json

# Or search without dashes
cass search "workspace /data" --workspace /path --json
```

---

## Output Problems

### Export Piping Causes Broken Pipe Panic

```bash
# WRONG (may panic):
cass export /path.jsonl --format json | head -100

# RIGHT:
cass export /path.jsonl --format json -o /tmp/out.json
jq '.[0:100]' /tmp/out.json
```

### Output Too Large

```bash
--fields minimal          # 5x smaller
--fields summary          # 2x smaller
--max-content-length 200  # Truncate snippets
--max-tokens 1200         # Soft cap
--aggregate date,agent    # Counts only
```

---

## Content Not Found

### String Exists But cass Returns 0 Hits

cass doesn't index everything. Large tool outputs (stdout/stderr) are skipped.

```bash
# Fallback to direct grep:
rg -n "the exact string" /path/from/source_path.jsonl
```

### Subagent Content Not Found

Subagent sessions are separate files.

```bash
cass search "KEYWORD" --workspace /path --json --fields minimal \
  | jq '[.hits[] | select(.source_path | contains("subagent"))]'
```

---

## jq Problems

### jq Returns null

```bash
| jq 'keys'                    # Top-level keys
| jq '.hits[0] | keys'         # Hit structure
| jq '.hits // []'             # Safe access with default
```

### Complex Filter Fails Silently

**Simplify rather than debug:**

```bash
| jq '.hits | length'          # Do we have hits?
| jq '.hits[0]'                # What does a hit look like?
| jq '.hits[0] | keys'         # What fields exist?
```

---

## Diagnostic Workflow

When cass isn't working:

```bash
# 1. Health check
cass status --json

# 2. Refresh index
cass index --json

# 3. Diagnostics
cass diag --json

# 4. Simple query test
cass search "*" --workspace /path --limit 5 --json

# 5. Check workspace paths
cass search "test" --aggregate workspace --json

# 6. Fallback to raw grep
rg -n "exact string" /path/to/session.jsonl
```

### Timestamp Reality Check

```bash
cass search "*" --workspace /path --aggregate date --limit 1 --json \
  | jq '.aggregations.date.buckets | sort_by(.key) | reverse | .[0]'
# Should show today's date if you've been working today
```

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | Success | Continue |
| `1` | Error (index, query) | Check `cass status`, review query |
| `2` | Invalid args, special chars | Quote query, simplify, check flags |

---

## Pro Tips

### Parallel Searches Find More

Lexical matching is literal. Different phrasings = different hits.

```bash
cass search "cass search" --workspace /path --json --fields minimal &
cass search "aggregate" --workspace /path --json --fields minimal &
cass search "line_number" --workspace /path --json --fields minimal &
wait
```

Together = full coverage.
