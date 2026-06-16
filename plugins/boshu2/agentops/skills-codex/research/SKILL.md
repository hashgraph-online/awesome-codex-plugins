---
name: research
description: "Run research."
---

# Research Skill

> **Quick Ref:** Deep codebase exploration with multi-angle analysis. Output: `.agents/research/*.md`

```bash
ao codex ensure-start 2>/dev/null || true
```

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

**CLI dependencies:** ao (knowledge injection — optional). If ao is unavailable, skip prior knowledge search and proceed with direct codebase exploration.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--auto` | off | Skip human approval gate. Used by `$rpi --auto` for fully autonomous lifecycle. |

## Execution Steps

Given `$research <topic> [--auto]`:

### Step 1: Create Output Directory
```bash
mkdir -p .agents/research
```

### Step 2: Check Prior Art

**First, search and inject existing knowledge (if ao available):**

```bash
# Pull relevant prior knowledge for this topic
ao lookup --query "<topic>" --limit 5 2>/dev/null || \
  ao search "<topic>" 2>/dev/null || \
  echo "ao not available, skipping knowledge search"
```

**Apply retrieved knowledge (mandatory when results returned):**

If ao returns relevant learnings or patterns, do NOT just load them as passive context. For each returned item:
1. Check: does this learning apply to the current research topic? (answer yes/no)
2. If yes: note how it shapes your research direction — what questions does it answer? what areas does it warn about?
3. Cross-reference prior findings against new discoveries in your research output
4. Cite applicable learnings by filename in the research document's Findings section

After applying, record each citation:
```bash
ao metrics cite "<learning-path>" --type applied 2>/dev/null || true
```

Also look for:
- Prior research on this topic or related topics
- Known patterns or anti-patterns
- Lessons learned from similar investigations

**Search ALL local knowledge locations by content (not just filename):**

Use Grep to search every knowledge directory for the topic. This catches learnings from `$post-mortem`, brainstorms, and plans — not just research artifacts.

```bash
# Search all knowledge locations by content
for dir in research learnings knowledge patterns retros plans brainstorm; do
  grep -r -l -i "<topic>" .agents/${dir}/ 2>/dev/null
done

# Search global patterns (cross-repo knowledge)
grep -r -l -i "<topic>" ~/.agents/patterns/ 2>/dev/null
```

If matches are found, read the relevant files before proceeding to exploration. Prior knowledge prevents redundant investigation.

### Step 2.5: Pre-Flight — Detect Spawn Backend

Before launching the explore agent, detect which backend is available:

1. Check if `spawn_agent` is available → log `"Backend: codex-sub-agents"`
5. Else → log `"Backend: inline (no spawn available)"`

Record the selected backend — it will be included in the research output document for traceability.

**Read the matching backend reference for concrete tool call examples:**
- Codex → `references/backend-codex-subagents.md`
- Background Tasks → `references/backend-background-tasks.md`
- Inline → `references/backend-inline.md`

### Effort and Session Hints

- Set effort to `low` for explore agents — research is breadth-first scanning, not deep reasoning.
- Use `--from-pr <url>` to scope research to a specific PR's changed files when investigating PR-related topics.

### Step 3: Launch Explore Agent

**YOU MUST DISPATCH AN EXPLORATION AGENT NOW.** Select the backend using capability detection:

#### Backend Selection (MANDATORY)

1. If `spawn_agent` is available → **Codex sub-agent**
2. Else → **Background task fallback**

#### Exploration Prompt (all backends)

Use this prompt for whichever backend is selected. The exploration uses **iterative retrieval** (see `references/iterative-retrieval.md`): start broad, score relevance, extract new search terms from high-relevance files, and repeat for up to 3 cycles.

```
Thoroughly investigate: <topic>

Use iterative retrieval: after each discovery tier, score results 0-1 for relevance.
From files scoring 0.5+, extract new search terms (function names, imports, config keys).
Use extracted terms in subsequent tiers. Max 3 refinement cycles.

Discovery tiers (execute in order, skip if source unavailable):

Tier 1 — Code-Map (fastest, authoritative):
  Read docs/code-map/README.md → find <topic> category
  Read docs/code-map/{feature}.md → get exact paths and function names
  Skip if: no docs/code-map/ directory

Tier 2 — Semantic Search (conceptual matches):
  mcp__smart-connections-work__lookup query="<topic>" limit=10
  Skip if: MCP not connected

Tier 2.5 — Git History (recent changes and decision context):
  git log --oneline -30 -- <topic-related-paths>   # scoped to relevant paths, cap 30 lines
  git log --all --oneline --grep="<topic>" -10      # cap 10 matches
  git blame <key-file> | grep -i "<topic>" | head -20  # cap 20 lines
  Skip if: not a git repo, no relevant history, or <topic> too broad (>100 matches)
  NEVER: git log on full repo without -- path filter (same principle as Tier 3 scoping)
  NOTE: This is git commit history, not session history. For session/handoff history, use $recover.

Tier 3 — Scoped Search (keyword precision):
  Grep("<topic>", path="<specific-dir>/")   # ALWAYS scope to a directory
  Glob("<specific-dir>/**/*.py")            # ALWAYS scope to a directory
  NEVER: Grep("<topic>") or Glob("**/*.py") on full repo — causes context overload

Tier 4 — Source Code (verify from signposts):
  Read files identified by Tiers 1-3 (including git history leads from Tier 2.5)
  Use function/class names, not line numbers

Tier 5 — Prior Knowledge (may be stale):
  Search ALL .agents/ knowledge dirs by content:
    for dir in research learnings knowledge patterns retros plans brainstorm; do
      grep -r -l -i "<topic>" .agents/${dir}/ 2>/dev/null
    done
  Read matched files. Cross-check findings against current source.

Tier 6 — External Docs (last resort):
  WebSearch for external APIs or standards
  Only when Tiers 1-5 are insufficient

Return a detailed report with:
- Key files found (with paths)
- How the system works
- Important patterns or conventions
- Any issues or concerns

Cite specific file:line references for all claims.
```

#### Spawn Research Agents

If your runtime supports spawning parallel subagents, spawn one or more research agents with the exploration prompt. Each agent explores independently and writes findings to `.agents/research/`.

If no multi-agent capability is available, perform the exploration **inline** in the current session using file reading, grep, and glob tools directly.

### Step 4: Validate Research Quality (mandatory in auto mode)

**For thorough research, perform quality validation:**

**Auto mode enforcement:** When `--auto` is set, quality validation is mandatory. If depth rating < 2 for any critical area (Step 4b), emit WARN and log to `.agents/research/quality-warning.md`. In interactive mode, this step remains optional.

#### 4a. Coverage Validation
Check: Did we look everywhere we should? Any unexplored areas?
- List directories/files explored
- Identify gaps in coverage
- Note areas that need deeper investigation

#### 4b. Depth Validation
Check: Do we UNDERSTAND the critical parts? HOW and WHY, not just WHAT?
- Rate depth (0-4) for each critical area
- Flag areas with shallow understanding
- Identify what needs more investigation

#### 4c. Gap Identification
Check: What DON'T we know that we SHOULD know?
- List critical gaps
- Prioritize what must be filled before proceeding
- Note what can be deferred

#### 4d. Assumption Challenge
Check: What assumptions are we building on? Are they verified?
- List assumptions made
- Flag high-risk unverified assumptions
- Note what needs verification

### Step 5: Synthesize Findings

After the Explore agent and validation swarm return, write findings to:
`.agents/research/YYYY-MM-DD-<topic-slug>.md`

Use this format:
```markdown
---
id: research-YYYY-MM-DD-<topic-slug>
type: research
date: YYYY-MM-DD
---

# Research: <Topic>

**Backend:** <codex-sub-agents | claude-native-teams | background-task-fallback | inline>
**Scope:** <what was investigated>

## Summary
<2-3 sentence overview>

## Key Files
| File | Purpose |
|------|---------|
| path/to/file.py | Description |

## Findings
<detailed findings with file:line citations>

## Recommendations
<next steps or actions>
```

### Step 5.5: Persist Reusable Findings

After the research artifact is written, identify any reusable findings that should influence future work.

Persist only reusable findings, not transient observations, to `.agents/findings/registry.jsonl` using the finding-registry contract:

- include provenance fields: `source.repo`, `source.session`, `source.file`, `source.skill`
- require `dedup_key`, `pattern`, `detection_question`, `checklist_item`, `applicable_when`, and `confidence`
- keep lifecycle fields explicit: `status`, `superseded_by`, `ttl_days`, `hit_count`, `last_cited`
- merge by `dedup_key`
- use the contract's temp-file-plus-rename atomic write rule

After the registry update, if `hooks/finding-compiler.sh` exists, run:

```bash
bash hooks/finding-compiler.sh --quiet 2>/dev/null || true
```

This refreshes promoted findings and compiled prevention outputs in the same session.

### Step 6: Request Human Approval (Gate 1)

**Skip this step if `--auto` flag is set.** In auto mode, proceed directly to Step 7.

Ask the operator for approval:

```
Parameters:
  questions:
    - question: "Research complete. Approve to proceed to planning?"
      header: "Gate 1"
      options:
        - label: "Approve"
          description: "Research is sufficient, proceed to $plan"
        - label: "Revise"
          description: "Need deeper research on specific areas"
        - label: "Abandon"
          description: "Stop this line of investigation"
      multiSelect: false
```

**Wait for approval before reporting completion.**

### Step 7: Report to User

Tell the user:
1. What you found
2. Where the research doc is saved
3. Gate 1 approval status
4. Next step: `$plan` to create implementation plan

## Key Rules

- **Actually dispatch the Explore agent** - don't just describe doing it
- **Scope searches** - use the topic to narrow file patterns
- **Cite evidence** - every claim needs `file:line`
- **Write output** - research must produce a `.agents/research/` artifact

## Thoroughness Levels

Include in your Explore agent prompt:
- "quick" - for simple questions
- "medium" - for feature exploration
- "very thorough" - for architecture/cross-cutting concerns

For onboarding-style research ("what does this do?", new repo orientation), follow `references/onboarding-methodology.md` for the phased docs-first walk and reusable mental-model template. When the question reduces to "what happens when <event> arrives?", trace one path end-to-end using `references/data-flow-from-entry-points.md`.

## Examples

### Investigate Authentication System

**User says:** `$research "authentication system"`

**What happens:**
1. Agent searches knowledge base for prior auth research
2. Explore agent investigates via Code-Map, Grep, and file reading
3. Findings synthesized with file:line citations
4. Output written to `.agents/research/2026-02-13-authentication-system.md`

**Result:** Detailed report identifying auth middleware location, session handling, and token validation patterns.

### Quick Exploration of Cache Layer

**User says:** `$research "cache implementation"`

**What happens:**
1. Agent uses Glob to find cache-related files
2. Explore agent reads key files and summarizes current state
3. No prior research found, proceeds with fresh exploration
4. Output written to `.agents/research/2026-02-13-cache-implementation.md`

**Result:** Summary of cache strategy, TTL settings, and eviction policies with file references.

### Deep Dive into Payment Flow

**User says:** `$research "payment processing flow"`

**What happens:**
1. Agent loads prior payment research from knowledge base
2. Explore agent traces flow through multiple services
3. Identifies integration points and error handling
4. Output written with cross-service file citations

**Result:** End-to-end payment flow diagram with file paths and critical decision points.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Research too shallow | Default exploration depth insufficient for the topic | Re-run with broader scope or specify additional search areas |
| Research output too large | Exploration covered too many tangential areas | Narrow the goal to a specific question rather than a broad topic |
| Missing file references | Codebase has changed since last exploration or files are in unexpected locations | Use Glob to verify file locations before citing them. Always use absolute paths |
| Auto mode skips important areas | Automated exploration prioritizes breadth over depth | Remove `--auto` flag to enable human approval gate for guided exploration |
| Explore agent times out | Topic too broad for single exploration pass | Split into smaller focused topics (e.g., "auth flow" vs "entire auth system") |
| No backend available for spawning | Running in environment without spawn_agent support | Research runs inline — still functional but slower |

## Reference Documents

- [references/iterative-retrieval.md](references/iterative-retrieval.md)
- [references/deep-research-mcp.md](references/deep-research-mcp.md)
- [references/backend-background-tasks.md](references/backend-background-tasks.md)
- [references/backend-codex-subagents.md](references/backend-codex-subagents.md)
- [references/backend-inline.md](references/backend-inline.md)
- [references/context-discovery.md](references/context-discovery.md)
- [references/data-flow-from-entry-points.md](references/data-flow-from-entry-points.md)
- [references/document-template.md](references/document-template.md)
- [references/failure-patterns.md](references/failure-patterns.md)
- [references/onboarding-methodology.md](references/onboarding-methodology.md)
- [references/ralph-loop-contract.md](references/ralph-loop-contract.md)
- [references/source-discovery-and-pattern-extraction.md](references/source-discovery-and-pattern-extraction.md)
- [references/vibe-methodology.md](references/vibe-methodology.md)
- [../shared/references/backend-background-tasks.md](../shared/references/backend-background-tasks.md)
- [../shared/references/backend-codex-subagents.md](../shared/references/backend-codex-subagents.md)
- [../shared/references/backend-inline.md](../shared/references/backend-inline.md)
- [../shared/references/ralph-loop-contract.md](../shared/references/ralph-loop-contract.md)
- [references/codebase-archaeology.md](references/codebase-archaeology.md) — Systematic codebase exploration for onboarding
- [references/software-research.md](references/software-research.md) — Research tools via source code, GitHub, and web
