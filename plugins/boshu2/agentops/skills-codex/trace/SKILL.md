---
name: trace
description: "Run trace."
---
# Trace Skill

> **Quick Ref:** Trace design decisions through CASS sessions, handoffs, git, and artifacts. Output: `.agents/research/YYYY-MM-DD-trace-*.md`

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## When to Use

- Trace HOW architectural decisions evolved
- Find WHEN a concept was introduced
- Understand WHY something was designed a certain way
- Build provenance chain for design decisions

For knowledge artifact lineage (learnings, patterns, tiers), use `$provenance` instead.

**CLI dependencies:** cass (session search). If cass is unavailable, skip transcript search and rely on git log, handoff docs, and `.agents/` artifacts for decision tracing.

## Execution Steps

Given `$trace <concept>`:

### Step 1: Classify Target Type

Determine what kind of provenance to trace:

```
IF target is a file path (contains "/" or "."):
  → Use $provenance (artifact lineage)

IF target is a git ref (sha, branch, tag):
  → Use git-based tracing (Step 2b)

ELSE (keyword/concept):
  → Use design decision tracing (Step 2a)
```

### Step 2a: Design Decision Tracing (Concepts)

Launch 4 parallel search agents (CASS, Handoff, Git, Research) and wait for all to complete.

**Backend:** Agents use `spawn_agent` or `codex exec` for parallel exploration. See `../shared/SKILL.md` ("Backend Detection") for the shared contract.

Read `references/discovery-patterns.md` for agent definitions and prompts.

### Step 2b: Git-Based Tracing (Commits/Refs)

Read `references/discovery-patterns.md` for git-based tracing commands.

### Step 3: Build Timeline

Merge results from all sources into a single chronological timeline (oldest first). Deduplicate same-day/same-session events. Every claim needs a source citation.

### Step 4: Extract Key Decisions

For each event in timeline, identify:
- **What changed:** The decision or evolution
- **Why:** Reasoning if available
- **Who:** Session/author/commit author
- **Evidence:** Link to source (session path, file, commit)

### Step 5: Write Trace Report

**Write to:** `.agents/research/YYYY-MM-DD-trace-<concept-slug>.md`

Read `references/report-template.md` for the full report format and deduplication rules.

### Step 6: Report to User

Tell the user:
1. Concept traced successfully
2. Timeline of evolution (key dates)
3. Most significant decisions
4. Location of trace report
5. Related concepts to explore

## Handling Edge Cases

Read `references/edge-cases.md` for handling: no CASS results, no handoffs, ambiguous concepts (>20 results), and all-sources-empty scenarios. General principle: continue with remaining sources and note gaps in the report.

## Key Rules

- **Search ALL sources** - CASS, handoffs, git, research
- **Build timeline** - chronological evolution is the goal
- **Cite evidence** - every claim needs a source
- **Handle gaps gracefully** - not all concepts are in all sources
- **Write report** - trace must produce `.agents/research/` artifact

## Relationship to $provenance

| Skill | Purpose | Input | Output |
|-------|---------|-------|--------|
| `$provenance` | Artifact lineage | File path | Tier/promotion history |
| `$trace` | Design decisions | Concept/keyword | Timeline of evolution |

Use `$provenance` for: "Where did this learning come from?"
Use `$trace` for: "How did we decide on this architecture?"

## Examples

```bash
# Trace a design decision
$trace "three-level architecture"

# Trace a role/concept
$trace "Chiron"

# Trace a pattern
$trace "brownian ratchet"

# Trace a feature
$trace "parallel wave execution"
```

### Tracing an Architectural Decision

**User says:** `$trace "agent team protocol"`

**What happens:**
1. Agent classifies target as concept (not file path or git ref)
2. Agent launches 4 parallel agents: CASS search, handoff search, git log search, research artifact search
3. CASS finds 8 sessions mentioning "agent team", handoff finds 2 docs, git finds 3 commits, research finds 1 analysis
4. Agent builds chronological timeline from 2026-01-15 (first mention) to 2026-02-08 (latest update)
6. Agent writes trace report to `.agents/research/2026-02-13-trace-agent-team-protocol.md` with full timeline and citations

**Result:** Complete evolution timeline showing how agent team protocol developed across 7 sessions with source citations.

### Tracing from Git Commit

**User says:** `$trace abc1234`

**What happens:**
1. Agent detects git ref format (short sha)
2. Agent runs git-based tracing commands to get commit details, changed files, related commits
3. Agent uses `git log --grep` to find related work
4. Agent searches `.agents/` for contemporary research/plans
5. Agent builds timeline focused on that specific change
6. Agent writes report showing commit context, what changed, why (from commit message and related docs)

**Result:** Trace report links commit to broader design context from surrounding artifacts.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| CASS returns no results | Session search not installed or query too specific | Check `which cass`. If missing, skip CASS and rely on handoffs/git/research. Try broader query terms. |
| Timeline has gaps | Not all decisions documented in searchable artifacts | Note gaps in report. Suggest interviewing team members or checking Slack/email archives for missing context. |
| Too many results (>50 matches) | Very broad concept or high-frequency term | Read `references/edge-cases.md` for ambiguous concept handling. Narrow query or filter by date range. Ask user for more specific aspect to trace. |
| Empty trace report (all sources failed) | Concept genuinely undocumented or typo | Verify spelling. Try synonyms. Report to user: "No documented history found. This may be a new concept or may need different search terms." |

## Local Resources

### references/

- [references/discovery-patterns.md](references/discovery-patterns.md)
- [references/edge-cases.md](references/edge-cases.md)
- [references/report-template.md](references/report-template.md)

### scripts/

- `scripts/validate.sh`


