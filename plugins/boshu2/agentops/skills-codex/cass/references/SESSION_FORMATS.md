# Session File Formats by Agent

> **Critical knowledge for parsing raw session logs.** Each agent stores conversations in JSONL with different structures.

## Contents

- [Quick Detection](#quick-detection)
- [Claude Code Format](#claude-code-format)
- [Codex CLI Format](#codex-cli-format)
- [Gemini CLI Format](#gemini-cli-format)
- [Subagent Sessions (Critical)](#subagent-sessions-critical)
- [Universal Extraction Patterns](#universal-extraction-patterns)
- [File Location Cheat Sheet](#file-location-cheat-sheet)
- [Quick Reference](#quick-reference)

---

## Quick Detection

```bash
# Detect agent type from first line
head -1 /path/to/session.jsonl | jq -e '.type == "user"' && echo "claude_code"
head -1 /path/to/session.jsonl | jq -e '.role == "user"' && echo "codex_or_gemini"
```

---

## Claude Code Format

**Location:** `~/.claude/projects/<escaped-workspace-path>/*.jsonl`

**Path encoding:** Workspace `/data/projects/foo` becomes `-data-projects-foo`

**Example path:**
```
~/.claude/projects/-data-projects-beads_rust-2d7a3b1/session-20260116-143022.jsonl
```

### Message Structure

```json
{"type": "user", "message": {"content": "...", "role": "user"}, "timestamp": "2026-01-16T14:30:22Z"}
{"type": "assistant", "message": {"content": [...], "role": "assistant"}, "timestamp": "..."}
{"type": "tool_result", "tool_use_id": "...", "content": "...", "timestamp": "..."}
```

### Content Formats

**User content** — can be string OR array:
```json
// Simple string
{"type": "user", "message": {"content": "Help me fix this bug"}}

// Array with text blocks (common with images/files)
{"type": "user", "message": {"content": [{"type": "text", "text": "Help me fix this bug"}]}}
```

**Assistant content** — always array with mixed types:
```json
{"type": "assistant", "message": {"content": [
  {"type": "text", "text": "I'll help you fix that..."},
  {"type": "tool_use", "id": "toolu_01...", "name": "Read", "input": {"file_path": "/path/to/file"}}
]}}
```

### Extract User Messages

```bash
# Simple extraction (handles both string and array content)
jq 'select(.type == "user") | .message.content | if type == "array" then [.[] | select(.type == "text") | .text] | join(" ") else . end' session.jsonl
```

### Extract Tool Calls

```bash
# All tool calls
jq 'select(.type == "assistant") | .message.content[] | select(.type == "tool_use") | {name, input}' session.jsonl

# Specific tool (e.g., Write)
jq 'select(.type == "assistant") | .message.content[] | select(.type == "tool_use" and .name == "Write")' session.jsonl

# Tool results
jq 'select(.type == "tool_result")' session.jsonl
```

### First User Prompt (The Ritual Opener)

```bash
# Line 1-3 typically contains the opening prompt
jq -s '[.[] | select(.type == "user")][0] | .message.content' session.jsonl
```

---

## Codex CLI Format

**Location:** `~/.codex/**/*.jsonl` (varies by installation)

### Message Structure

```json
{"role": "user", "content": "...", "timestamp": "2026-01-16T14:30:22Z"}
{"role": "assistant", "content": "...", "created_at": "..."}
```

### Key Differences from Claude Code

| Aspect | Claude Code | Codex |
|--------|-------------|-------|
| Type field | `.type == "user"` | `.role == "user"` |
| Timestamp | `.timestamp` | `.timestamp` or `.created_at` |
| Content structure | Often array | Usually string |
| Tool calls | Embedded in `.content[]` | Varies |

### Extract User Messages

```bash
jq 'select(.role == "user") | .content' session.jsonl
```

### Extract with Timestamp

```bash
jq 'select(.role == "user") | {ts: (.timestamp // .created_at), content}' session.jsonl
```

---

## Gemini CLI Format

**Location:** `~/.gemini/**/*.jsonl` (varies by installation)

Similar to Codex format. Uses `.role` instead of `.type`.

```bash
jq 'select(.role == "user") | .content' session.jsonl
```

---

## Subagent Sessions (Critical)

**What:** When Claude Code spawns a Task agent, it creates a separate session log.

**Location:** `~/.claude/projects/<workspace>/subagents/agent-<id>.jsonl`

### Subagent Structure

```
Line 1: Session metadata (type, model info)
Line 2: THE USER PROMPT (this is gold — the extraction prompt that worked)
Line 3+: Agent execution and responses
```

### Why Subagents Matter

Deep dive extraction prompts live here. The prompt at line 2 is copy-paste ready — it's the exact instruction that produced the extraction.

### Extract Subagent Prompt

```bash
# View prompt with context
cass view /path/subagents/agent-XXXXX.jsonl -n 2 -C 1

# Extract just the text
sed -n '2p' /path/subagents/agent-XXXXX.jsonl | jq '.message.content'

# Or with jq slurp
jq -s '.[1].message.content' /path/subagents/agent-XXXXX.jsonl
```

### Find All Subagent Sessions

```bash
# Via cass search
cass search "KEYWORD" --workspace /path --json --fields minimal \
  | jq '[.hits[] | select(.source_path | contains("subagent"))] | .[].source_path' -r | sort -u

# Via filesystem
find ~/.claude/projects -path "*/subagents/*.jsonl" | head -20
```

---

## Universal Extraction Patterns

### Detect and Extract (Any Agent)

```bash
#!/bin/bash
# extract_prompts.sh — works with any agent format

FILE="$1"

# Detect format and extract
if jq -e '.[0].type == "user"' "$FILE" >/dev/null 2>&1; then
    # Claude Code format
    jq -s '[.[] | select(.type == "user")] | .[] | .message.content' "$FILE"
elif jq -e '.[0].role == "user"' "$FILE" >/dev/null 2>&1; then
    # Codex/Gemini format
    jq -s '[.[] | select(.role == "user")] | .[] | .content' "$FILE"
else
    echo "Unknown format"
fi
```

### Count Messages by Type

```bash
# Claude Code
jq -s 'group_by(.type) | map({type: .[0].type, count: length})' session.jsonl

# Codex/Gemini
jq -s 'group_by(.role) | map({role: .[0].role, count: length})' session.jsonl
```

### Extract Conversation Flow

```bash
# Timeline of who said what
jq -s '[.[] | {
  type: (.type // .role),
  ts: (.timestamp // .created_at),
  preview: (if .message then .message.content else .content end | tostring[0:100])
}]' session.jsonl
```

---

## File Location Cheat Sheet

| Agent | Session Location | Subagent Location |
|-------|------------------|-------------------|
| Claude Code | `~/.claude/projects/<escaped-path>/*.jsonl` | `.../subagents/agent-*.jsonl` |
| Codex | `~/.codex/**/*.jsonl` | Varies |
| Gemini | `~/.gemini/**/*.jsonl` | Varies |

### Find Session Files for a Workspace

```bash
# Claude Code: convert workspace to escaped pattern
WORKSPACE="/data/projects/beads_rust"
ESCAPED=$(echo "$WORKSPACE" | tr '/' '-' | sed 's/^-//')
find ~/.claude/projects -name "*.jsonl" | grep -i "$ESCAPED"
```

---

## Quick Reference

| Task | Claude Code | Codex/Gemini |
|------|-------------|--------------|
| Is user message? | `.type == "user"` | `.role == "user"` |
| Get content | `.message.content` | `.content` |
| Get timestamp | `.timestamp` | `.timestamp` or `.created_at` |
| Tool call? | `.type == "tool_use"` | Varies |
| First prompt | `jq -s '[.[] \| select(.type=="user")][0]'` | `jq -s '[.[] \| select(.role=="user")][0]'` |
