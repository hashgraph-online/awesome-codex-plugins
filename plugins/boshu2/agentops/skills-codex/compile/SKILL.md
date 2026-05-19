---
name: compile
description: 'Compile .agents knowledge wiki.'
---
# Compile — Knowledge Compiler

Reads raw `.agents/` artifacts and compiles them into a structured, interlinked
markdown wiki. Inspired by Karpathy's LLM Knowledge Bases architecture.

## What This Skill Does

The knowledge flywheel captures signal reactively (via `$retro`, `$post-mortem`,
`$forge`). `$compile` closes the loop by:

1. **Mining** unextracted signal from git and `.agents/` (existing)
2. **Growing** learnings via validation, synthesis, and gap detection (existing)
3. **Compiling** raw artifacts into interlinked wiki articles (core value)
4. **Linting** the compiled wiki for contradictions, orphans, and gaps
5. **Defragging** stale and duplicate artifacts (existing)

**No vector DB.** At personal scale (~100-400 articles), the compiled wiki fits
in context windows. The wiki IS the retrieval layer.

**Output:** `.agents/compiled/` — encyclopedia-style markdown with `[[backlinks]]`,
`index.md` catalog, and `log.md` chronological record.

## Pluggable Compute Backend

Set `AGENTOPS_COMPILE_RUNTIME` to pick the LLM backend:

| Value | Backend | Notes |
|-------|---------|-------|
| `ollama` | Ollama API | Needs `OLLAMA_HOST` (default `http://localhost:11434`). |
| `openai` | OpenAI-compatible | Needs `OPENAI_API_KEY`. |

When unset, `ao compile` attempts to auto-detect a local CLI backend. If none
is available, headless compile fails fast with an actionable error.

### Large-corpus batching

`ao compile --batch-size N` caps changed files per LLM prompt (default 25),
so a 2000+ file corpus splits into batches instead of one giant prompt.
Pair with `--max-batches N` to cap work per invocation; remaining files are
picked up on the next run.

## Execution Steps

### Step 0: Setup

```bash
mkdir -p .agents/compiled
```

Determine mode from arguments:
- `$compile` — Full cycle: Mine → Grow → Compile → Lint → Defrag
- `$compile --compile-only` — Skip mine/grow, just compile + lint
- `$compile --lint-only` — Only lint the existing compiled wiki
- `$compile --defrag-only` — Only run defrag/cleanup
- `$compile --mine-only` — Only run mine + grow (legacy behavior)

### Step 1 — Mine: Extract Signal

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

### Step 2 — Grow: LLM-Driven Synthesis

This is the reasoning phase. Perform each sub-step using tool calls.

**Flywheel Health Diagnostic:** Compute σ (consistency), ρ (velocity), δ (decay) and report escape velocity status. See `references/flywheel-diagnostics.md` for measurement commands and remediation actions.

**2a. Validate Top Learnings and Adjust Confidence**

Select the 5 most recent files from `.agents/learnings/`. For each:
1. Read the learning file (including its `confidence` and `scope` frontmatter)
2. If it references a function or file path, verify the code still exists
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

### Step 3 — Compile: Build the Wiki

**This is the core phase.** The LLM reads all raw `.agents/` artifacts and
compiles them into structured, interlinked wiki articles.

**3a. Inventory Source Artifacts**

Scan all compilable directories:

```bash
find .agents/learnings .agents/patterns .agents/research .agents/retros \
     .agents/forge .agents/knowledge -type f -name "*.md" 2>/dev/null | sort
```

For each file, compute a content hash. Compare against `.agents/compiled/.hashes.json`
(previous compilation hashes). Files with unchanged hashes skip compilation (incremental mode).

**3b. Extract Topics and Entities**

Read each changed source artifact. Extract:
- **Topics**: major themes (e.g., "testing strategy", "CI pipeline", "knowledge flywheel")
- **Entities**: specific tools, files, patterns, people referenced
- **Relationships**: which topics connect to which entities

Group artifacts by topic. Each topic becomes a wiki article.

**3c. Compile Articles**

For each topic, compile an encyclopedia-style article:

**If `AGENTOPS_COMPILE_RUNTIME` is set**, the compilation backend is selected
automatically via the environment variable. No script invocation needed.

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

Write `.agents/compiled/.hashes.json` with file-to-hash mappings for incremental compilation.

### Step 4 — Lint: Wiki Health Check

Scan the compiled wiki for quality issues.

**4a. Contradictions** — Compare claims across articles. Flag conflicting assertions.

**4b. Orphan Pages** — Find articles with zero inbound `[[backlinks]]`.

**4c. Missing Cross-References** — Find articles discussing same topics but not linking.

**4d. Stale Claims** — Verify code references still exist.

**4e. Coverage Gaps** — Flag source artifacts that contributed to zero wiki articles.

**4f. Write Lint Report** — Write `.agents/compiled/lint-report.md` with health score.

### Step 5 — Defrag: Mechanical Cleanup

Run cleanup to find stale, duplicate, and oscillating artifacts.

```bash
ao defrag --prune --dedup
```

Read `.agents/defrag/latest.json` and note: orphaned learnings (unreferenced, >30 days
old), near-duplicate pairs (>80% content similarity), and oscillating goals (alternating
improved/fail for 3+ cycles).

**Fallback:** `find .agents/learnings -name "*.md" -mtime +30` for stale files.

### Normalization Defect Scan

During defrag, scan the learnings and patterns pool for structural defects:
- PLACEHOLDER → HIGH (empty knowledge pollutes retrieval)
- STACKED_FRONTMATTER → MEDIUM (parsing errors, possible data loss)
- BUNDLED → HIGH (breaks per-learning citation tracking)
- DUPLICATE_HEADING → LOW (cosmetic, may confuse extraction)

### Step 6 — Report

Write `.agents/compile/YYYY-MM-DD-report.md` with compilation summary, lint summary,
new learnings proposed, validations, knowledge gaps, and defrag summary.

## Scheduling / Auto-Trigger

Lightweight defrag (prune + dedup, no mining or compilation) runs automatically at
session end via the `compile-session-defrag.sh` hook.

For full compilation, invoke `$compile` manually or schedule the headless
compiler script with your host OS:

```bash
# Example: external cron entry for nightly compilation
0 3 * * * cd /path/to/repo && AGENTOPS_COMPILE_RUNTIME=ollama bash skills-codex/compile/scripts/compile.sh --force
```

AgentOps exposes this flow through `ao compile`. If you want unattended
compilation, use your host scheduler (`launchd`, `cron`, `systemd`, CI, etc.)
to invoke `ao compile --force --runtime ollama` or call the lower-level
`bash skills-codex/compile/scripts/compile.sh` directly.
If you want the broader private overnight loop, use `ao overnight start`
instead of inventing a parallel Dream wrapper inside `$compile`.

## Interactive Modes

These modes describe the interactive `$compile` skill behavior:

| Mode | Description |
|------|-------------|
| `--compile-only` | Skip mine/grow, just compile + lint |
| `--lint-only` | Only lint the existing compiled wiki |
| `--defrag-only` | Only run defrag/cleanup |
| `--mine-only` | Only run mine + grow (legacy behavior) |
| `--full` | Full cycle: mine → grow → compile → lint → defrag |
| `--since 26h` | Time window for the mine phase |
| `--incremental` | Skip unchanged source files (hash-based) |
| `--force` | Recompile all articles regardless of hashes |

## Headless Script Flags

For unattended runs, `bash skills-codex/compile/scripts/compile.sh` supports:

| Flag | Default | Description |
|------|---------|-------------|
| `--sources <dir>` | `.agents` | Source root for learnings, patterns, research, retros, forge, and knowledge |
| `--output <dir>` | `.agents/compiled` | Target directory for compiled wiki output |
| `--incremental` | on | Skip unchanged source files (hash-based) |
| `--force` | off | Recompile all articles regardless of hashes |
| `--lint-only` | off | Only run the lint pass on the existing compiled wiki |
| `--full` | on | Accepted for parity; default behavior already runs the full headless compile path |

## Examples

**User says:** `$compile` — Full Mine → Grow → Compile → Lint → Defrag cycle.

**User says:** `$compile --compile-only` — Just compile raw artifacts into wiki.

**User says:** `$compile --lint-only` — Scan existing wiki for health issues.

**User says:** `$compile --since 7d` — Mines with a wider window (7 days).

**Pre-evolve warmup:** Run `$compile` before `$evolve` for a fresh, validated knowledge base.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ao mine` not found | ao CLI not in PATH | Use manual fallback in Step 1 |
| No orphaned research | All research already referenced | Skip 2b, proceed to synthesis |
| Empty mine output | No recent activity | Widen `--since` window |
| Oscillation sweep empty | No oscillating goals | Healthy state — no action needed |
| Ollama connection refused | Tunnel not running or wrong host | Run `ssh -L 11435:localhost:11435 bushido-windows` or check `OLLAMA_HOST` |
| Compilation too slow | Large corpus on small model | Use `--incremental` or switch to larger model |

## Reference Documents

- [references/phases.md](references/phases.md) — full per-phase procedure (mine → grow → compile → lint → defrag → report)
- [references/confidence-scoring.md](references/confidence-scoring.md)
- [references/flywheel-diagnostics.md](references/flywheel-diagnostics.md)
- [references/knowledge-synthesis-patterns.md](references/knowledge-synthesis-patterns.md)

## Local Resources

### scripts/

- `scripts/validate.sh`
