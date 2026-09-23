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
| User prompts | Inspect source record roles; line positions and titles are not roles |
| Candidate subagent paths | `contains("subagent")`; verify native parent/child metadata |
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

### User Prompt Extraction

Search hits locate candidates; they are not a role filter. Use the returned
path and line with bounded `cass pack`, `view` or `expand`, then identify the
role from the actual record. Early lines can be metadata or assistant content,
and user messages can occur anywhere. Verify that the returned path/line
matches the requested hit; missing files, absent roles and clamped windows
remain retrieval gaps.

```bash
cass search "KEYWORD" --workspace /path --mode lexical --json --fields minimal --limit 20
cass view /path/from/hit.jsonl -n LINE -C 3 --json
cass expand /path/from/hit.jsonl --line LINE --context 3 --json
```

See [Raw Session File Parsing](#raw-session-file-parsing) for role-based
examples over an already selected, authorized excerpt. A title count is not a
count of user prompts.

### Subagent Session Extraction

```bash
# Find subagent sessions
| jq '[.hits[] | select(.source_path | contains("subagent"))]'

# Just paths (unique)
| jq '[.hits[] | select(.source_path | contains("subagent"))] | .[].source_path' -r | sort -u

# Candidate locations to inspect for native roles
| jq '[.hits[] | select(.source_path | contains("subagent")) | {source_path, line_number}]'
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

### Find Recurring Candidate Titles

```bash
# Count titles within this limited hit set; retain locations for review.
cass search "KEYWORD" --workspace /path --json --fields summary --limit 50 \
  | jq '[.hits[] | {title, source_path, line_number}]
    | group_by(.title)
    | map({title: .[0].title, hit_count: length, locations: .})
    | sort_by(-.hit_count) | .[0:20]'
```

Repeated titles can represent multiple hits in one session, copied text or
retries. They do not establish distinct prompt counts, user roles or success.
Inspect a selected candidate's intent, outcome and corrections before reuse.
Rare failures and scope decisions can matter even when the count is one.

---

## Raw Session File Parsing

Prefer CASS pack/view/expand. These examples apply only to an already selected,
authorized and bounded native excerpt named `excerpt.jsonl`, when a demonstrated
precision gap requires raw records. Never run them over an entire session by
default. The [source-format reference](SESSION_FORMATS.md) owns harness details;
unknown formats remain unknown.

### Claude Code Format

```bash
# Extract user messages
jq 'select(.type == "user") | .message.content' excerpt.jsonl

# Handle content arrays (common)
jq 'select(.type == "user") | .message.content | if type == "array" then [.[] | select(.type == "text") | .text] | join(" ") else . end' excerpt.jsonl

# With timestamps
jq 'select(.type == "user") | {ts: .timestamp, content: .message.content}' excerpt.jsonl

# First user record in this excerpt (not necessarily the session opener)
jq -s '[.[] | select(.type == "user")][0] | .message.content' excerpt.jsonl

# All user messages sorted
jq -s '[.[] | select(.type == "user")] | sort_by(.timestamp)' excerpt.jsonl
```

### Flat Codex/Gemini Format

```bash
# Extract user messages
jq 'select(.role == "user") | .content' excerpt.jsonl

# With timestamp
jq 'select(.role == "user") | {ts: (.timestamp // .created_at), content}' excerpt.jsonl

# First user prompt
jq -s '[.[] | select(.role == "user")][0] | .content' excerpt.jsonl
```

### Current Codex Records

```bash
jq 'select(.type == "response_item" and .payload.type == "message" and .payload.role == "user")
  | {ts: .timestamp, content: .payload.content}' excerpt.jsonl
```

Inspect record shape before selecting a parser. A metadata record at the start
cannot determine the role of subsequent messages. Avoid counting both a native
message and a duplicated event representation as separate user turns.

---

## Tool Call Extraction

### Find Tool Usage in Claude Code

```bash
# All tool calls
jq 'select(.type == "assistant") | .message.content[] | select(.type == "tool_use") | {name, input}' excerpt.jsonl

# Specific tool (e.g., Write)
jq 'select(.type == "assistant") | .message.content[] | select(.type == "tool_use" and .name == "Write")' excerpt.jsonl

# Tool results
jq 'select(.type == "tool_result")' excerpt.jsonl

# Count tool calls by type
jq -s '[.[] | select(.type == "assistant") | .message.content[]? | select(.type == "tool_use") | .name] | group_by(.) | map({tool: .[0], count: length}) | sort_by(-.count)' excerpt.jsonl
```

---

## Subagent Prompt Extraction

Use the selected hit's locator, not a fixed line number. A subagent filename is
a discovery clue; confirm native identity and relationships before attribution.

```bash
cass view /path/to/subagents/agent-XXXXX.jsonl -n LINE -C 3 --json
cass expand /path/to/subagents/agent-XXXXX.jsonl --line LINE --context 3 --json
```

Verify the record role and returned locator. Then apply the appropriate
role-based parser to a selected authorized excerpt if necessary.

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

### Bounded Evidence Pack

```bash
timeout 30 cass pack "KEYWORD" --workspace /path --mode lexical --json \
  --limit 20 --max-sessions 3 --max-evidence 6 --max-tokens 4000
```

Inspect selection and omission markers and actual returned locators. A citation
verification flag is not proof that the source still exists, that a requested
record was returned or that the excerpt establishes an outcome.

### Extract Conversation Flow from Session

```bash
jq -s '[.[] | {
  type: (.type // .role),
  ts: (.timestamp // .created_at),
  preview: (if .message then .message.content else .content end | tostring[0:100])
}]' excerpt.jsonl
```

### Find Sessions with Specific Tool Usage

```bash
cass search "Write" --workspace /path --json --fields minimal --limit 50 \
  | jq '[.hits[] | .source_path] | unique'
```

### Follow a Selected Hit

```bash
cass search "KEYWORD" --workspace /path --json --fields minimal --limit 20
# Select a relevant hit within the authorized source scope, then inspect it.
cass expand /path/from/selected-hit.jsonl --line LINE --context 3 --json
```

Do not bulk-open every returned path or assume the first user message is the
relevant prompt. Report missing or mismatched source records explicitly.

---

## Debugging jq

### The Golden Rule: Simplify Rather Than Debug

When a complex jq command fails silently or returns nothing:

**Don't:** Spend time debugging the complex filter.
**Do:** Simplify to basics, verify data exists, then rebuild.

```bash
# Complex filter fails silently:
| jq '[.hits[] | select(.source_path | contains("subagent"))] | ...'
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

# Add a candidate path filter
| jq '[.hits[] | select(.source_path | contains("subagent"))]'
```

### Check Intermediate Counts

```bash
| jq '.hits | length'                        # Total hits
| jq '[.hits[] | select(.source_path | contains("subagent"))] | length'  # After path filter
```

---

## One-Liners for Common Tasks

| Task | One-Liner |
|------|-----------|
| Candidate titles | `jq '[.hits[].title]'`; not role or outcome evidence |
| Source paths only | `jq '.hits[].source_path' -r` |
| Agent counts | `jq '.aggregations.agent.buckets'` |
| Date counts | `jq '.aggregations.date.buckets'` |
| First hit details | `jq '.hits[0]'` |
| Total matches | `jq '.total_matches'` |
| Unique titles | `jq '[.hits[].title] \| unique'` |
| Subagent paths | `jq '[.hits[] \| select(.source_path \| contains("subagent"))] \| .[].source_path' -r` |
