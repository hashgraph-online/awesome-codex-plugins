# Workflow Recipes

> **Priority:** Your prompts first. They're replicable. Agent execution varies.

## Contents

| Recipe | When |
|--------|------|
| [Session Bootstrap](#session-bootstrap) | Start of every cass session |
| [Ritual Discovery](#ritual-discovery) | Find reusable prompts |
| [User Prompt Extraction](#user-prompt-extraction) | What did I ask? |
| [Subagent Mining](#subagent-mining) | Find extraction prompts |
| [Scope Archaeology](#scope-archaeology) | When did we decide X? |
| [Multi-Agent Analysis](#multi-agent-analysis) | Who did what? |
| [Timeline Construction](#timeline-construction) | What happened when? |
| [Session Clustering](#session-clustering) | Find related work |
| [Context Recovery](#context-recovery) | Where did forgotten context resurface? |
| [Artifact Origin Tracing](#artifact-origin-tracing) | When was this doc created? |
| [Meta-Pattern: cass-on-cass](#meta-pattern-cass-on-cass) | Find which cass queries worked |
| [Full Example](#full-example) | End-to-end workflow demo |

---

## Session Bootstrap

**Always start here:**

```bash
# 1. Health check
cass status --json

# 2. Refresh index
cass index --json

# 3. Project overview
cass search "*" --workspace /data/projects/PROJECT --aggregate agent,date --limit 1 --json
```

---

## Ritual Discovery

**Goal:** Find prompts you used repeatedly (these work).

```bash
# Count suspected ritual
cass search "First read ALL" --workspace /path --json --limit 100 | jq '.total_matches'
# > 10 = RITUAL — document it

# Find most repeated prompts
cass search "*" --workspace /path --json --limit 500 \
  | jq '[.hits[] | select(.line_number <= 3) | .title[0:80]] | group_by(.) | map({prompt: .[0], count: length}) | sort_by(-.count) | .[0:20]'
```

### Common Rituals to Search

| Pattern | Purpose |
|---------|---------|
| `"First read ALL"` | Context loading |
| `"read AGENTS.md"` | Project rules |
| `"comprehensive deep dive"` | Thorough analysis |
| `"think super hard"` | Quality mode |
| `"ultrathink"` | Quality mode |
| `"extract all"` | Data extraction |

---

## User Prompt Extraction

**Goal:** Find what you asked, in what order.

```bash
# User prompts mention keyword (lines 1-3)
cass search "KEYWORD" --workspace /path --json --limit 100 \
  | jq '[.hits[] | select(.line_number <= 3)] | .[] | {path: .source_path, line: .line_number, title: .title[0:80]}'

# Count user prompts with term
cass search "KEYWORD" --workspace /path --json --limit 100 \
  | jq '[.hits[] | select(.line_number <= 3)] | length'

# View actual prompt
cass view /path/from/hit.jsonl -n 1 -C 5
```

---

## Subagent Mining

**Goal:** Extract deep dive prompts — line 2 of subagent logs is THE prompt.

```bash
# Find subagent sessions
cass search "deep dive" --workspace /path --json --fields minimal \
  | jq '[.hits[] | select(.source_path | contains("subagent"))] | .[].source_path' -r | sort -u

# View the prompt (line 2)
cass view /path/to/subagents/agent-XXXXX.jsonl -n 2 -C 1

# Extract just the text
sed -n '2p' /path/to/subagents/agent-XXXXX.jsonl | jq '.message.content'
```

### Subagent Structure

```
Line 1: Metadata
Line 2: THE PROMPT (gold — copy-paste ready)
Line 3+: Execution
```

---

## Scope Archaeology

**Goal:** Find where scope decisions were made.

### Exclusion Decisions

```bash
cass search "EXCLUDE" --workspace /path --json --limit 50
cass search "NOT porting" --workspace /path --json --limit 50
cass search "skip for now" --workspace /path --json --limit 50
cass search "out of scope" --workspace /path --json --limit 50
```

### Inclusion Decisions

```bash
cass search "we DO need" --workspace /path --json --limit 50
cass search "must include" --workspace /path --json --limit 50
cass search "actually necessary" --workspace /path --json --limit 50
```

### Scope Reduction

```bash
cass search "less invasive" --workspace /path --json --limit 50
cass search "simplify" --workspace /path --json --limit 50
cass search "reduce scope" --workspace /path --json --limit 50
```

---

## Multi-Agent Analysis

**Goal:** Understand which agent did which work.

```bash
# Overview by agent
cass search "*" --workspace /path --aggregate agent --limit 1 --json \
  | jq '.aggregations.agent.buckets'

# Search within specific agent
cass search "KEYWORD" --workspace /path --agent claude_code --json --limit 50
cass search "KEYWORD" --workspace /path --agent codex --json --limit 50

# Compare activity over time
cass search "*" --workspace /path --agent claude_code --aggregate date --limit 1 --json
```

### Agent Patterns

| Agent | Typical Work |
|-------|--------------|
| Claude Code (Opus) | Complex reasoning, architecture, specs |
| Codex | Fast extraction, high-volume, code gen |
| Gemini | Research, varied tasks |

---

## Timeline Construction

**Goal:** Build chronological understanding of work.

### Method 1: Date Aggregation (Recommended)

```bash
cass search "*" --workspace /path --aggregate date --limit 1 --json \
  | jq '.aggregations.date.buckets | sort_by(.key) | .[] | "\(.key): \(.count) hits"' -r
```

### Method 2: Timeline Command

```bash
cass timeline --since 2026-01-14 --until 2026-01-17 --workspace /path --json
cass timeline --since 7d --json
```

**Note:** Aggregations usually have simpler, more predictable JSON.

### Method 3: Manual Grouping

```bash
cass search "*" --workspace /path --json --limit 200 \
  | jq '[.hits[] | {date: .created_at[0:10], path: .source_path}] | group_by(.date) | .[] | {date: .[0].date, count: length}'
```

---

## Session Clustering

**Goal:** Find all related work from one good hit.

```bash
# 1. Find one relevant session
cass search "KEYWORD" --workspace /path --json --fields summary --limit 5
# Get source_path

# 2. Discover related
cass context /path/from/hit.jsonl --json

# 3. Iterate over related_sessions
```

**Why:** Work happens in clusters. One good session → whole cluster.

---

## Context Recovery

**Goal:** Find where forgotten context was recovered (reveals what mattered).

```bash
cass search "we already DID" --workspace /path --json --limit 50
cass search "wait we already" --workspace /path --json --limit 50
cass search "I think we discussed" --workspace /path --json --limit 50
cass search "earlier session" --workspace /path --json --limit 50
cass search "use cass to find" --workspace /path --json --limit 50
```

---

## Artifact Origin Tracing

**Goal:** Find when/how specific documents were created.

### Find References to Spec Documents

```bash
cass search "PLAN_TO_PORT_" --workspace /path --json --fields summary
cass search "EXISTING_" --workspace /path --json --fields summary
cass search "PROPOSED_ARCHITECTURE" --workspace /path --json --fields summary
```

### Find Creation Prompts

```bash
cass search "create a spec" --workspace /path --json
cass search "document this" --workspace /path --json
cass search "write to file" --workspace /path --json
```

---

## Meta-Pattern: cass-on-cass

**Goal:** Find which cass queries worked.

```bash
cass search "cass search" --workspace /path --json --fields minimal
cass search "aggregate" --workspace /path --json --fields minimal
```

**Insight:** Queries that appear multiple times = queries that worked.

---

## Full Example

```bash
# 1. Health
cass status --json

# 2. Overview (925 sessions)
cass search "*" --workspace /data/projects/beads_rust --aggregate agent --limit 1 --json

# 3. Find ritual opener
cass search "First read ALL of AGENTS.md" --workspace /data/projects/beads_rust --json --limit 100 \
  | jq '.total_matches'
# Result: 50+ = RITUAL

# 4. Extract ritual
cass view $(cass search "First read ALL" --workspace /data/projects/beads_rust --json --limit 1 | jq -r '.hits[0].source_path') -n 1 -C 5

# 5. Find scope decisions
cass search "EXCLUDE" --workspace /data/projects/beads_rust --json --limit 50

# 6. Discover related
cass context /path/to/interesting/session.jsonl --json
```
