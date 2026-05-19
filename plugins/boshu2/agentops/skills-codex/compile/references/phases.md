# Compile Phases

Detailed per-phase reference for the `$compile` skill. Moved out of
SKILL.md to keep that file within the 248-line skill-lint budget. The
top-level SKILL.md now carries the flag surface, runtime table, and a
pointer to this doc.

## Step 0: Setup

```bash
mkdir -p .agents/compiled
```

Determine mode from arguments:
- `/compile` — Full cycle: Mine → Grow → Compile → Lint → Defrag
- `/compile --compile-only` — Skip mine/grow, just compile + lint
- `/compile --lint-only` — Only lint the existing compiled wiki
- `/compile --defrag-only` — Only run defrag/cleanup
- `/compile --mine-only` — Only run mine + grow (legacy behavior)

## Step 1 — Mine: Extract Signal

Run mechanical extraction. Mine scans git history, `.agents/research/`, and code
complexity hotspots for patterns never captured as learnings.

```bash
ao mine --since 26h                    # default: all sources, last 26h
ao mine --since 7d --sources git,agents  # wider window, specific sources
```

Read `.agents/mine/latest.json` and extract: co-change clusters (files changing
together), orphaned research (unreferenced `.agents/research/` files), and complexity
hotspots (high-CC functions with recent edits).

**Fallback (no ao CLI):** Use `git log --since="7 days ago" --name-only` to find
recurring file groups. List `.agents/research/*.md` and check references in learnings.

**Assign Initial Confidence.** For every new learning candidate extracted, assign a
confidence score based on evidence strength:

| Evidence | Score | Rationale |
|----------|-------|-----------|
| Single session observation | 0.3 | Anecdotal — seen once, may not generalize |
| Explicit user correction or post-mortem finding | 0.5 | Demonstrated — user-validated signal |
| Pattern observed in 2+ sessions | 0.6 | Repeated — likely real, not coincidence |
| Validated across multiple sessions or projects | 0.7 | Strong — safe to auto-apply |
| Battle-tested, never contradicted | 0.9 | Near-certain — always apply |

Also assign a **scope** tag: `project:<name>` (project-specific), `language:<lang>`
(language convention), or `global` (universal pattern). Default to `project:<current>`
unless the pattern is clearly language- or tool-universal.

Write the confidence and scope into the learning frontmatter:

```yaml
---
title: "Learning title"
confidence: 0.3
scope: project:agentops
observed_in:
  - session: "YYYY-MM-DD"
    context: "Brief description of observation"
---
```

## Step 2 — Grow: LLM-Driven Synthesis

This is the reasoning phase. Perform each sub-step using tool calls.

**Flywheel Health Diagnostic:** Compute σ (consistency), ρ (velocity), δ (decay) and report escape velocity status. See `flywheel-diagnostics.md` for measurement commands and remediation actions.

**2a. Validate Top Learnings and Adjust Confidence**

Select the 5 most recent files from `.agents/learnings/`. For each:
1. Read the learning file (including its `confidence` and `scope` frontmatter)
2. If it references a function or file path, use Read to verify the code still exists
3. Classify as: **validated** (matches), **stale** (changed), or **contradicted** (opposite)
4. **Adjust confidence** based on validation result:
   - Validated and still accurate: **+0.1** (cap at 0.9)
   - Stale but partially true: **no change** (mark for review)
   - Contradicted by current code: **-0.2** (floor at 0.1, flag for removal)
   - Pattern validated in a new project: **+0.15**
   - Not referenced in 30+ days: **-0.05** (time decay)
   - Not referenced in 90+ days: **-0.1** (time decay)

Update the learning file frontmatter with the new confidence score.

**Auto-Promotion Rule:** After confidence adjustment, check if the learning's
confidence is **> 0.7**. If so, and it is not already in MEMORY.md, promote it:
1. Add the learning's key insight to the relevant MEMORY.md topic file
2. Log: `"Promoted '<title>' to MEMORY.md (confidence: <score>)"`
3. If the same pattern appears in 2+ projects with confidence >= 0.8, promote its
   scope from `project:<name>` to `global`

**2b. Rescue Orphaned Research**

For each orphaned research file from mine output: read it, summarize the key insight
in 2-3 sentences, and propose as a new learning candidate with title and category.

**2c. Cross-Domain Synthesis**

Group mine findings by theme (e.g., "testing patterns", "CLI conventions"). For themes
with 2+ findings, write a synthesized pattern candidate capturing the common principle.

**2d. Gap Identification**

Compare mine output topics against existing learnings. Topics with no corresponding
learning are knowledge gaps. List each with: topic, evidence, suggested learning title.

## Step 3 — Compile: Build the Wiki

**This is the core new phase.** The LLM reads all raw `.agents/` artifacts and
compiles them into structured, interlinked wiki articles.

**3a. Inventory Source Artifacts**

Scan all compilable directories:

```bash
find .agents/learnings .agents/patterns .agents/research .agents/retros \
     .agents/forge .agents/knowledge -type f -name "*.md" 2>/dev/null | sort
```

For each file, compute a content hash:

```bash
md5sum "$file" | cut -d' ' -f1
```

Compare against `.agents/compiled/.hashes.json` (previous compilation hashes).
Files with unchanged hashes skip compilation (incremental mode).

**3b. Extract Topics and Entities**

Read each changed source artifact. Extract:
- **Topics**: major themes (e.g., "testing strategy", "CI pipeline", "knowledge flywheel")
- **Entities**: specific tools, files, patterns, people referenced
- **Relationships**: which topics connect to which entities

Group artifacts by topic. Each topic becomes a wiki article.

**3c. Compile Articles**

For each topic, compile an encyclopedia-style article:

**If `AGENTOPS_COMPILE_RUNTIME` is set**, use `scripts/compile.sh`:

```bash
AGENTOPS_COMPILE_RUNTIME=ollama scripts/compile.sh \
  --sources .agents/ \
  --output .agents/compiled/ \
  --incremental
```

**If running inline** (no runtime set), compile directly:

For each topic group, write a wiki article to `.agents/compiled/<topic-slug>.md`:

```markdown
---
title: "<Topic Title>"
compiled: "YYYY-MM-DD"
sources:
  - .agents/learnings/example.md
  - .agents/research/example.md
tags: [topic1, topic2]
---

# <Topic Title>

<2-3 paragraph synthesis of all source artifacts on this topic.
Not a summary — a compiled understanding that connects the dots
across multiple observations.>

## Key Insights

- <Insight 1> — from [[source-article-1]]
- <Insight 2> — from [[source-article-2]]

## Related

- [[other-topic-1]] — <why related>
- [[other-topic-2]] — <why related>

## Sources

- `source1.md` — .agents/learnings/source1.md
- `source2.md` — .agents/research/source2.md
```

Use `[[backlinks]]` (Obsidian-style wikilinks) for cross-references between articles.

**3d. Build Index**

Write `.agents/compiled/index.md`:

```markdown
# Knowledge Wiki — Index

> Auto-compiled from .agents/ corpus. Last updated: YYYY-MM-DD.
> Articles: N | Sources: N | Topics: N

## By Category

### <Category 1>
- [[article-1]] — one-line summary
- [[article-2]] — one-line summary

### <Category 2>
- [[article-3]] — one-line summary
```

**3e. Append to Log**

Append to `.agents/compiled/log.md`:

```markdown
## [YYYY-MM-DD] compile | <N> articles from <M> sources
- New: <list of new articles>
- Updated: <list of updated articles>
- Unchanged: <count> (skipped, hashes match)
```

**3f. Save Hashes**

Write `.agents/compiled/.hashes.json`:

```json
{
  ".agents/learnings/example.md": "abc123...",
  ".agents/patterns/example.md": "def456..."
}
```

## Step 4 — Lint: Wiki Health Check

Scan the compiled wiki for quality issues. This is the Karpathy "lint pass."

**4a. Contradictions**

Compare claims across articles. Flag pairs where one article asserts X and
another asserts not-X or a conflicting recommendation.

**4b. Orphan Pages**

Find articles with zero inbound `[[backlinks]]` from other articles.
These are disconnected knowledge — either missing links or low-value articles.

**4c. Missing Cross-References**

Find articles that discuss the same entities/topics but don't link to each other.

**4d. Stale Claims**

For articles referencing specific code (file paths, function names), verify
the code still exists. Flag stale references.

**4e. Coverage Gaps**

Compare the topic list against the source artifacts. Flag source artifacts
that contributed to zero wiki articles (un-compiled knowledge).

**4f. Write Lint Report**

Write `.agents/compiled/lint-report.md`:

```markdown
# Wiki Lint Report — YYYY-MM-DD

## Contradictions: N
- [[article-a]] vs [[article-b]]: <description>

## Orphan Pages: N
- [[orphan-1]], [[orphan-2]]

## Missing Cross-References: N
- [[article-x]] should link to [[article-y]] (shared topic: <topic>)

## Stale Claims: N
- [[article-z]] references `path/to/deleted.go` (line N)

## Coverage Gaps: N
- .agents/learnings/uncovered.md — not compiled into any article

## Health Score: N/100
```

## Step 5 — Defrag: Mechanical Cleanup

Run cleanup to find stale, duplicate, and oscillating artifacts.

```bash
ao defrag --prune --dedup
```

Read `.agents/defrag/latest.json` and note: orphaned learnings (unreferenced, >30 days
old), near-duplicate pairs (>80% content similarity), and oscillating goals (alternating
improved/fail for 3+ cycles).

**Fallback:** `find .agents/learnings -name "*.md" -mtime +30` for stale files.
Check `.agents/evolve/cycle-history.jsonl` for alternating result patterns.

### Normalization Defect Scan

During defrag, scan the learnings and patterns pool for structural defects that degrade flywheel quality:

```bash
# Placeholder patterns: files with only frontmatter, no content after closing ---
for f in .agents/patterns/**/*.md .agents/learnings/**/*.md; do
  [ -f "$f" ] || continue
  content_after_frontmatter=$(awk '/^---$/{n++; if(n==2) found=1; next} found{print}' "$f" | grep -c '[^ ]')
  [ "$content_after_frontmatter" -eq 0 ] && echo "PLACEHOLDER: $f"
done

# Stacked frontmatter: multiple --- delimiter pairs (>2 occurrences of ^---$)
grep -rl '^---$' .agents/learnings/ .agents/patterns/ 2>/dev/null | while read f; do
  count=$(grep -c '^---$' "$f")
  [ "$count" -gt 2 ] && echo "STACKED_FRONTMATTER: $f ($count delimiters)"
done

# Bundled multi-learning files: more than one ## Learning heading
grep -rl '^## Learning' .agents/learnings/ 2>/dev/null | while read f; do
  count=$(grep -c '^## Learning' "$f")
  [ "$count" -gt 1 ] && echo "BUNDLED: $f ($count learnings in one file)"
done

# Duplicated headings within a file
for f in .agents/learnings/**/*.md .agents/patterns/**/*.md; do
  [ -f "$f" ] || continue
  dupes=$(grep '^## ' "$f" | sort | uniq -d)
  [ -n "$dupes" ] && echo "DUPLICATE_HEADING: $f — $dupes"
done
```

**Report normalization defects** in the defrag output. If any are found, list them with severity:
- PLACEHOLDER → HIGH (empty knowledge pollutes retrieval)
- STACKED_FRONTMATTER → MEDIUM (parsing errors, possible data loss)
- BUNDLED → HIGH (breaks per-learning citation tracking)
- DUPLICATE_HEADING → LOW (cosmetic, may confuse extraction)

## Step 6 — Report

```bash
mkdir -p .agents/compile
```

Write `.agents/compile/YYYY-MM-DD-report.md`:

```markdown
# Compile Report — YYYY-MM-DD

## Compilation Summary
- Articles compiled: N (new: N, updated: N, unchanged: N)
- Source artifacts processed: N
- Topics identified: N
- Backlinks created: N

## Lint Summary
- Health score: N/100
- Contradictions: N | Orphans: N | Stale claims: N | Gaps: N

## New Learnings Proposed
- [title]: [summary] (source: [research file or synthesis])

## Validations
- Validated: N | Stale: N (list files) | Contradicted: N (list with explanation)

## Knowledge Gaps
- [topic]: [evidence] → suggested learning: "[title]"

## Defrag Summary
- Orphaned: N | Duplicates: N | Oscillating goals: N

## Recommendations
1. [Actionable next step]
```

If `bd` is available, create issues for knowledge gaps:

```bash
bd add "[Knowledge Gap] <topic>" --label knowledge --label compile
```
