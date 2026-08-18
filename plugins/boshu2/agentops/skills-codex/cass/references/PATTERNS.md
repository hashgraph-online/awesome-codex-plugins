# jq Extraction Patterns

> **Copy-paste reference** for parsing cass output and raw session files.

## Contents

- [Quick Reference Card](#quick-reference-card)
- [cass Search Output](#cass-search-output)
- [Pattern Detection](#pattern-detection)
- [Raw Session File Parsing](#raw-session-file-parsing)
- [Tool Call Extraction](#tool-call-extraction)
- [Subagent Prompt Extraction](#subagent-prompt-extraction)
- [Safe Access Patterns](#safe-access-patterns)
- [Composite Recipes](#composite-recipes)
- [Debugging jq](#debugging-jq)
- [One-Liners for Common Tasks](#one-liners-for-common-tasks)

---

## Quick Reference Card

| Goal | Pattern |
|------|---------|
| User prompts (lines 1-5) | `select(.line_number <= 3)` |
| Subagent sessions | `contains("subagent")` |
| Total match count | `.total_matches` |
| Safe access with default | `// []` or `// "default"` |
| Sort descending | `sort_by(-.field)` |
| Group and count | `group_by(.) \| map({key: .[0], count: length})` |
| Claude Code user message | `.type == "user"` |
| Codex/Gemini user message | `.role == "user"` |
| Tool call | `.type == "tool_use"` |

---

## cass Search Output

### Basic Hit Extraction

```bash
# First 5 hits
| jq '.hits[0:5]'

# Just source paths (for follow-up)
| jq '.hits[].source_path' -r

# Path, line number, title
| jq '[.hits[] | {path: .source_path, line: .line_number, title: .title[0:80]}]'

# Total match count
| jq '.total_matches'
```

### User Prompt Extraction (The Most Important Pattern)

User prompts appear at lines 1-5. Filter by `line_number`:

```bash
# Get user prompts only
| jq '[.hits[] | select(.line_number <= 3)]'

# With formatted output
| jq '[.hits[] | select(.line_number <= 3)] | .[] | {path: .source_path, line: .line_number, title: .title[0:80]}'

# Just titles (for scanning)
| jq '[.hits[] | select(.line_number <= 3) | .title]'

# Count user prompts
| jq '[.hits[] | select(.line_number <= 3)] | length'
```

### Subagent Session Extraction

```bash
# Find subagent sessions
| jq '[.hits[] | select(.source_path | contains("subagent"))]'

# Just paths (unique)
| jq '[.hits[] | select(.source_path | contains("subagent"))] | .[].source_path' -r | sort -u

# User prompts in subagent sessions
| jq '[.hits[] | select(.source_path | contains("subagent")) | select(.line_number <= 3)]'
```

### Aggregation Parsing

```bash
# Agent breakdown
cass search "*" --workspace /path --aggregate agent --limit 1 --json \
  | jq '.aggregations.agent.buckets'

# Date breakdown
cass search "*" --workspace /path --aggregate date --limit 1 --json \
  | jq '.aggregations.date.buckets'

# Formatted timeline
| jq '.aggregations.date.buckets | sort_by(.key) | .[] | "\(.key): \(.count) hits"' -r

# Multiple aggregations
| jq '{agents: .aggregations.agent.buckets, dates: .aggregations.date.buckets}'
```

---

## Pattern Detection

### Find Repeated Prompts (Ritual Detection)

```bash
# Group prompts by title, count, sort by frequency
cass search "*" --workspace /path --json --limit 500 \
  | jq '[.hits[] | select(.line_number <= 3) | .title[0:80]] | group_by(.) | map({prompt: .[0], count: length}) | sort_by(-.count) | .[0:20]'
```

### Filter by Count Threshold

```bash
# Only patterns appearing 5+ times
| jq '[.hits[] | select(.line_number <= 3) | .title[0:80]] | group_by(.) | map({prompt: .[0], count: length}) | map(select(.count >= 5)) | sort_by(-.count)'
```

### Check Total Matches (Is It a Ritual?)

```bash
cass search "First read ALL" --workspace /path --json --limit 100 | jq '.total_matches'
# > 10 = ritual, document it
# < 3 = one-off, ignore
```

---

## Raw Session File Parsing

### Claude Code Format

```bash
# Extract user messages
jq 'select(.type == "user") | .message.content' session.jsonl

# Handle content arrays (common)
jq 'select(.type == "user") | .message.content | if type == "array" then [.[] | select(.type == "text") | .text] | join(" ") else . end' session.jsonl

# With timestamps
jq 'select(.type == "user") | {ts: .timestamp, content: .message.content}' session.jsonl

# First user prompt only (the ritual opener)
jq -s '[.[] | select(.type == "user")][0] | .message.content' session.jsonl

# All user messages sorted
jq -s '[.[] | select(.type == "user")] | sort_by(.timestamp)' session.jsonl
```

### Codex/Gemini Format

```bash
# Extract user messages
jq 'select(.role == "user") | .content' session.jsonl

# With timestamp
jq 'select(.role == "user") | {ts: (.timestamp // .created_at), content}' session.jsonl

# First user prompt
jq -s '[.[] | select(.role == "user")][0] | .content' session.jsonl
```

### Detect Format and Extract

```bash
# Check format
head -1 session.jsonl | jq -e '.type == "user"' && echo "claude_code"
head -1 session.jsonl | jq -e '.role == "user"' && echo "codex"
```

---

## Tool Call Extraction

### Find Tool Usage in Claude Code

```bash
# All tool calls
jq 'select(.type == "assistant") | .message.content[] | select(.type == "tool_use") | {name, input}' session.jsonl

# Specific tool (e.g., Write)
jq 'select(.type == "assistant") | .message.content[] | select(.type == "tool_use" and .name == "Write")' session.jsonl

# Tool results
jq 'select(.type == "tool_result")' session.jsonl

# Count tool calls by type
jq -s '[.[] | select(.type == "assistant") | .message.content[]? | select(.type == "tool_use") | .name] | group_by(.) | map({tool: .[0], count: length}) | sort_by(-.count)' session.jsonl
```

---

## Subagent Prompt Extraction

Subagent logs have THE prompt at line 2:

```bash
# View line 2 via cass
cass view /path/to/subagents/agent-XXXXX.jsonl -n 2 -C 1

# Extract with sed + jq
sed -n '2p' /path/to/subagents/agent-XXXXX.jsonl | jq '.message.content'

# Extract with jq slurp
jq -s '.[1].message.content' /path/to/subagents/agent-XXXXX.jsonl
```

---

## Safe Access Patterns

### Avoid null Errors

```bash
# With default
| jq '.hits // []'
| jq '.aggregations.agent.buckets // []'
| jq '.total_matches // 0'

# Check before access
| jq 'if .hits | length == 0 then "no results" else .hits[0:5] end'

# Safe iterate
| jq '(.hits // [])[]'
```

### Check JSON Structure

```bash
# Top-level keys
| jq 'keys'

# First hit structure
| jq '.hits[0] | keys'

# Check field exists
| jq '.hits[0] | has("source_path")'
```

---

## Composite Recipes

### Full Prompt Mining Pipeline

```bash
# 1. Search all sessions
cass search "*" --workspace /path --json --limit 500 \
  | jq '
    [.hits[] | select(.line_number <= 3) | .title[0:80]]
    | group_by(.)
    | map({prompt: .[0], count: length})
    | sort_by(-.count)
    | map(select(.count >= 2))
    | .[0:30]
  '
```

### Extract Conversation Flow from Session

```bash
jq -s '[.[] | {
  type: (.type // .role),
  ts: (.timestamp // .created_at),
  preview: (if .message then .message.content else .content end | tostring[0:100])
}]' session.jsonl
```

### Find Sessions with Specific Tool Usage

```bash
cass search "Write" --workspace /path --json --fields minimal --limit 50 \
  | jq '[.hits[] | .source_path] | unique'
```

### Complete Source Path → First Prompt Pipeline

```bash
# 1. Get source paths
cass search "KEYWORD" --workspace /path --json --fields minimal --limit 20 \
  | jq '.hits[].source_path' -r > /tmp/paths.txt

# 2. Extract first prompt from each
while read path; do
  echo "=== $path ==="
  jq -s '[.[] | select(.type == "user")][0] | .message.content[0:200]' "$path" 2>/dev/null
done < /tmp/paths.txt
```

---

## Debugging jq

### The Golden Rule: Simplify Rather Than Debug

When a complex jq command fails silently or returns nothing:

**Don't:** Spend time debugging the complex filter.
**Do:** Simplify to basics, verify data exists, then rebuild.

```bash
# Complex filter fails silently:
| jq '[.hits[] | select(.line_number <= 3 and .source_path | contains("subagent"))] | ...'
# No output, no error. Now what?

# SIMPLIFY FIRST:
| jq '.hits | length'           # Do we have hits at all?
| jq '.hits[0]'                 # What does a hit look like?
| jq '.hits[0] | keys'          # What fields exist?

# THEN rebuild step by step
```

**Why this works:** The JSON structure varies slightly between cass versions. Complex filters compound errors. Simple filters reveal the actual structure.

### Build Up Incrementally

```bash
# Start simple
| jq '.hits[0:5]'

# Add projection
| jq '[.hits[] | {path: .source_path, line: .line_number}]'

# Add filter
| jq '[.hits[] | select(.line_number <= 3)]'

# Combine (last)
| jq '[.hits[] | select(.line_number <= 3) | select(.source_path | contains("subagent"))]'
```

### Check Intermediate Counts

```bash
| jq '.hits | length'                        # Total hits
| jq '[.hits[] | select(.line_number <= 3)] | length'   # After line filter
| jq '[.hits[] | select(.source_path | contains("subagent"))] | length'  # After path filter
```

---

## One-Liners for Common Tasks

| Task | One-Liner |
|------|-----------|
| User prompt titles | `jq '[.hits[] \| select(.line_number <= 3) \| .title]'` |
| Source paths only | `jq '.hits[].source_path' -r` |
| Agent counts | `jq '.aggregations.agent.buckets'` |
| Date counts | `jq '.aggregations.date.buckets'` |
| First hit details | `jq '.hits[0]'` |
| Total matches | `jq '.total_matches'` |
| Unique titles | `jq '[.hits[].title] \| unique'` |
| Subagent paths | `jq '[.hits[] \| select(.source_path \| contains("subagent"))] \| .[].source_path' -r` |
