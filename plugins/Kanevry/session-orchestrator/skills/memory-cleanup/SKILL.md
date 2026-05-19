---
name: memory-cleanup
user-invocable: true
tags: [memory, maintenance, meta, dream]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when performing manual memory consolidation (Dream-equivalent). Reviews, consolidates, and prunes memory files
  under ~/.claude/projects/*/memory/. Run after major refactors, every 5+ sessions, or when memory
  quality degrades (broken links, stale references, contradictions, MEMORY.md > 200 lines).
  Invoke with /memory-cleanup.
---

# Memory Cleanup — Manual Dream Process

Implements the 4-phase memory consolidation process modelled after Claude Code's Auto Dream feature. Run after major refactors, framework migrations, or every 5+ sessions in a repo.

The memory system lives at `~/.claude/projects/<encoded-cwd>/memory/` and consists of:

- `MEMORY.md` — index file (must stay under 200 lines; lines after 200 are truncated by the harness).
- Topic files — one Markdown file per memory entry with YAML frontmatter (`name`, `description`, `metadata.type`).

The four memory types are `user`, `feedback`, `project`, `reference` (see global `auto memory` instructions for semantics). This skill never invents new types.

## Phase 1: Orient

Understand the current memory state before making changes.

1. List all files in the memory directory:
   ```bash
   ls -la ~/.claude/projects/*/memory/ 2>/dev/null | grep "$(basename "$(pwd)")"
   ```
   Or directly list the project's memory dir (the path is in the `auto memory` system instructions).

2. Read `MEMORY.md` (the index file) — note its line count:
   ```bash
   wc -l <memory-dir>/MEMORY.md
   ```

3. Skim each topic file referenced in the index. Build a mental map:
   - Which topics are covered?
   - Are there overlapping files?
   - Any files not referenced in the index?
   - Any index entries pointing to files that no longer exist?

**Goal**: Improve existing files, never create duplicates.

## Phase 2: Gather Signal

Find what's changed since the last consolidation.

1. **Git history** — recent commits give the timeline for "did this fact change?":
   ```bash
   git log --oneline -20
   ```

2. **Stale references** — for each file/function/symbol mentioned in memory, verify it still exists:
   ```bash
   grep -rn "specific-file-or-function" src/ lib/ scripts/ 2>/dev/null
   ```

3. **Relative dates** — find temporal references that need conversion:
   ```bash
   grep -rni "yesterday\|today\|tomorrow\|last week\|this week\|gestern\|heute\|morgen\|letzte woche" <memory-dir>/
   ```

4. **Version drift** — package versions stored in memory vs reality:
   ```bash
   cat package.json | grep '"version"'
   ```

5. **Test/issue-count drift** — claims like "5001 passed" or "8 open issues" age fast. Cross-check with current state if mentioned.

## Phase 3: Consolidate

Apply maintenance operations to memory files.

### 3a: Merge overlapping entries
If multiple files or entries describe the same thing, combine them into one authoritative entry. Update inbound `[[wiki-link]]`s accordingly.

### 3b: Convert relative dates to absolute
"Yesterday we decided X" → "On 2026-03-24 we decided X". Always use ISO date format (YYYY-MM-DD). This rule applies on **write**, but cleanup catches what slipped through.

### 3c: Remove stale references
- Delete entries about files that were removed during refactors.
- Remove debugging notes for bugs that are fixed.
- Update function/file paths that were renamed (`git log --diff-filter=R` surfaces renames).

### 3d: Update outdated facts
- Package versions that have been bumped.
- Test counts, issue counts, line counts that changed.
- Feature flags that were toggled.
- Architecture decisions that were reversed (keep a `decisions.md`-style note that the decision was reversed, with the reason — don't silently overwrite).

### 3e: Resolve contradictions
If two memory entries conflict, check the codebase to determine which is current. Delete the outdated entry. **Never leave contradictions.**

## Phase 4: Prune & Index

Keep `MEMORY.md` clean and under the 200-line limit.

1. **Check line count**:
   ```bash
   wc -l <memory-dir>/MEMORY.md
   ```

2. **If over 180 lines**, extract detailed content into topic files. Suggested naming:
   - Session summaries → `project_sessions.md` or `session-YYYY-MM-DD-<slug>.md`
   - Architecture decisions → `reference_decisions.md`
   - Package/tooling details → `reference_packages.md`
   - Use the convention: `{type}_{topic}.md`

3. **Topic file frontmatter** (required):
   ```yaml
   ---
   name: descriptive-name
   description: one-line description for relevance matching
   metadata:
     type: project   # one of: user | feedback | project | reference
   ---
   ```

4. **Update the index**:
   - `MEMORY.md` is an index, not a dump.
   - One-line `- [Title](file.md) — hook` entries.
   - Remove stale pointers to deleted files.
   - Add links for new topic files.
   - Reorder by relevance (most-accessed topics first).

5. **Final verification**:
   ```bash
   wc -l <memory-dir>/MEMORY.md  # must be < 200
   # verify all index links resolve to existing files
   grep -oP '\]\(([^)]+\.md)\)' <memory-dir>/MEMORY.md | sed 's/](\(.*\))/\1/' | while read f; do
     [ -f "<memory-dir>/$f" ] || echo "BROKEN: $f"
   done
   ```

## Output

After completing all four phases, report:

- Files created / updated / deleted (paths only — no full diffs in the chat output).
- `MEMORY.md` line count (before → after).
- Contradictions resolved (with one-line summary each).
- Stale entries pruned (count + categories).
- Any issues that need manual attention (e.g. ambiguous facts that need user input — surface via `AskUserQuestion` rather than guessing).

## Anti-Patterns

- **Don't rewrite memory you don't understand.** If a fact's provenance is unclear, leave it and flag it in the output instead of deleting.
- **Don't bulk-delete on the first run.** Cleanup runs are cheap; aggressive pruning costs context that can't easily be reconstructed.
- **Don't create new memory types.** The four-type taxonomy (`user`, `feedback`, `project`, `reference`) is load-bearing for the relevance heuristic.
- **Don't touch `MEMORY.md` if line-count is already healthy.** Re-ordering for its own sake creates churn without value.
