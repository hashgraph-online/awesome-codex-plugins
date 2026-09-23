# Workflow Recipes

> **Priority:** Resolve a concrete uncertainty with cited intent, action and outcome evidence.

## Contents

| Recipe | When |
|--------|------|
| [Search Readiness](#search-readiness) | Observe state when needed |
| [Recurring Candidates](#recurring-candidates) | Investigate repeated prompts |
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

## Search Readiness

After source, task, model and destination authorization, search a healthy or
stale-but-usable index immediately. Record freshness; do not automatically
refresh, rebuild or add `--refresh`. If unavailable, report that state or use
[bounded recovery](RECOVERY.md) only when needed and authorized.

```bash
timeout 15 cass status --json
# Optional overview when useful to the question
timeout 30 cass search "*" --workspace /data/projects/PROJECT --mode lexical \
  --aggregate agent,date --fields minimal --limit 1 --json
```

---

## Recurring Candidates

**Goal:** Investigate a recurring prompt without assuming that repetition means
it worked. Search for a task-relevant phrase, then review selected episodes.

```bash
timeout 30 cass search "TASK PHRASE" --workspace /path --mode lexical \
  --json --fields summary --limit 20
timeout 30 cass pack "TASK PHRASE" --workspace /path --mode lexical --json \
  --limit 20 --max-sessions 3 --max-evidence 6 --max-tokens 4000
```

Compare the user intent, action, result and later corrections. Recurrence may
come from copied instructions, repeated failure or retries. Check a competing
explanation or counterexample before reuse; later task evidence is needed to
show usefulness. No count threshold promotes a prompt into a rule.

---

## User Prompt Extraction

**Goal:** Find what the user asked and preserve its actual source identity.

```bash
cass search "KEYWORD" --workspace /path --mode lexical --json --fields minimal --limit 20
# Use the selected hit's path and line, not a presumed session opener.
cass view /path/from/hit.jsonl -n LINE -C 3 --json
cass expand /path/from/hit.jsonl --line LINE --context 3 --json
```

User roles come from native message records, including nested harness fields.
Line numbers and titles are not role evidence. Confirm that the returned
locator matches the request; unknown roles, absent sources and clamped windows
remain gaps. Selected excerpts do not establish all prompts or chronology for
unread parts of a session.

---

## Subagent Mining

**Goal:** Inspect a relevant subagent prompt and its observed outcome.

```bash
cass search "TASK PHRASE" --workspace /path --json --fields minimal --limit 20 \
  | jq '[.hits[] | select(.source_path | contains("subagent")) | {source_path, line_number}]'
cass expand /path/from/selected-hit.jsonl --line LINE --context 3 --json
```

The filename is only a candidate filter. Verify the actual record role and
native parent/child metadata; the prompt is not guaranteed to occupy line 2.

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

**Goal:** Discover candidate related work from one relevant hit.

```bash
# 1. Find one relevant session
cass search "KEYWORD" --workspace /path --json --fields summary --limit 5
# Get source_path

# 2. Discover related
cass context /path/from/hit.jsonl --json

# 3. Iterate over related_sessions
```

Related-session output is not a complete cluster or proof of native parentage.

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

Repeated queries are candidates. Inspect the resulting hits and the task outcome; repetition alone may indicate failed searches.

---

## Full Example

```bash
# 1. Discover within a selected authorized workspace and bounded query family.
timeout 30 cass search "scope decision" --workspace /data/projects/PROJECT \
  --mode lexical --json --fields minimal --limit 20

# 2. Ask CASS for a small cited selection.
timeout 30 cass pack "scope decision" --workspace /data/projects/PROJECT \
  --mode lexical --json --limit 20 --max-sessions 3 --max-evidence 6 --max-tokens 4000

# 3. Follow a relevant returned locator and check native role/intent/outcome.
timeout 15 cass expand /path/from/selected-hit.jsonl --line LINE --context 3 --json
```

Retain query, filters, limit, freshness, selected locators and omissions. Missing
sources or mismatched returned locations are not repaired by assuming an indexed
snippet is the original record. Reuse only what the observed evidence supports;
a justified no-change or insufficient-evidence result is valid.
