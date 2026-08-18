---
name: memory-cleanup
user-invocable: true
tags: [memory, maintenance, meta, dream]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
args-schema:
  - flag: --dry-run
    description: "Produce complete-body proposal in .orchestrator/pending-dream.md, no mutations."
  - flag: --apply-pending
    description: "Consume .orchestrator/pending-dream.md (atomic apply)."
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

## Argument Handling (Phase 0)

This skill accepts two optional flags. Default (no flag) runs the interactive 4-phase consolidation defined below.

| Flag | Behavior |
|---|---|
| `--dry-run` | Run Phases 1-3 read-only; instead of mutating MEMORY.md / topic files, write a complete-body MEMORY.md proposal (single fenced block — never a unified-diff) to `.orchestrator/pending-dream.md` (atomic). Exit 0. |
| `--apply-pending` | Read `.orchestrator/pending-dream.md`; refuse if older than 14 days (`stale`) or if MEMORY.md changed since the producing --dry-run (`stale-index`, #788); apply diff; delete pending file; print `auto-dream applied: -<X> lines, +<Y> entries`. Exit 0. |

Flags are mutually exclusive — passing both is an error. Absence of both = legacy interactive mode (Phases 1-4 below).

**`--dry-run` flow:**
- Read MEMORY.md and topic files (read-only).
- Produce the same internal plan the interactive mode would (merges, prunes, rewrites).
- **Serialisation contract (#717 — load-bearing, read before writing the proposal):** `applyPendingDream()` in `scripts/lib/auto-dream.mjs` consumes ONLY the FIRST fenced code block in the sidecar body and writes it VERBATIM as the complete new MEMORY.md. It does NOT parse or apply git-style diff hunks. Therefore the proposal MUST ALWAYS be the complete new MEMORY.md body, in EXACTLY ONE fenced ` ```markdown ` block — never git-style unified-diff hunks (`--- `/`+++ `/`@@ … @@` lines), and never multiple fences for MEMORY.md itself. Any topic-file (non-MEMORY.md) change needed by the plan CANNOT be carried inside that single fence — instead, append it AFTER the fence as a separate, clearly-delimited machine-readable section per topic file, using the heading `### Topic-file change: <path>` followed by plain-language instruction text (not a diff). These sections are for a human to apply by hand; `applyPendingDream()` never reads past the first fence. If a `### Topic-file change:` section needs to show illustrative code, use 4-space-indented code text, never a fenced ``` block — `countFencedBlocks()` counts every fence in the raw sidecar body (not just MEMORY.md's), so a second fence anywhere in the document trips the >1-fence unsupported-format guard and blocks the whole apply.
- Call `writePendingDream({ repoRoot, diff, sourceSession, memoryLinesBefore, proposedLinesAfter })` from `scripts/lib/auto-dream.mjs`, passing the single-fence MEMORY.md body (plus any `### Topic-file change:` sections) as `diff`.
- Print one-line status: `pending-dream written: <N> lines proposed` (or `no consolidation needed (MEMORY.md is healthy)` when the plan is empty).
- Exit 0 in both branches.

**`--apply-pending` flow:**
- Call `applyPendingDream({ repoRoot, memoryDir })` from `scripts/lib/auto-dream.mjs`.
- Behavior matrix on the helper return:
  - `applied: true` → print `auto-dream applied: -<linesBefore-linesAfter> lines, +<entries> consolidated entries` and exit 0.
  - `applied: false, reason: 'missing'` → print `no pending dream to apply` and exit 1.
  - `applied: false, reason: 'stale'` → print `pending dream is stale (>14d), re-run --dry-run` and exit 1.
  - `applied: false, reason: 'stale-index'` (#788) → print `MEMORY.md changed since the producing --dry-run; re-run --dry-run.` and exit 1. The sidecar is preserved and MEMORY.md is left untouched (MEMORY.md's mtime is newer than the sidecar's `generated_at`, so applying the frozen dry-run snapshot would clobber the interim edits).
  - `applied: false, reason: 'unsupported-format'` → print `auto-dream NOT applied: pending-dream.md contains git-style diff hunks this applier cannot consume. MEMORY.md left untouched, sidecar preserved. Re-run /memory-cleanup --dry-run to regenerate a complete-body proposal.` and exit 1.
- The sidecar file is deleted on successful apply; staleness (`stale` / `stale-index`), missing sidecar, or unsupported-format never deletes anything.

Both flag-driven flows delegate atomicity and staleness enforcement to `scripts/lib/auto-dream.mjs`. The interactive Phases 1-4 below remain unchanged.

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

## Phase 4.5: Worktree-Stale-Sweep (#575 P3.2)

> Skip if `persistence: false` in Session Config. Silent no-op if no Auto-promoted sibling worktrees exist or none are stale.

Detect stale Auto-promoted worktrees (older than `stale-branch-days` from Session Config, default 7 days) and offer them for batch-removal alongside the other housekeeping prune actions from Phase 4. This sub-phase is **additive** — it appends candidates to the existing prune flow rather than introducing a separate independent confirmation cycle.

### Detection: list candidate auto-promoted worktrees

Auto-promoted worktrees follow the layout `<parentDir>/<repoName>-<sessionId>/`, where `<sessionId>` is a semantic session-id (per `parseSessionId()` from `scripts/lib/session-id.mjs`). Random-suffix worktrees (UUID-format) are NOT auto-promoted and MUST be ignored.

> **Authoritative impl:** `scripts/lib/memory-cleanup/worktree-sweep.mjs` — `listAutoPromotedWorktrees(repoRoot, mainCheckoutRoot, opts)`. Import and call; do NOT re-implement from this doc.
>
> Algorithm: split `git worktree list --porcelain` on the blank-line delimiter; for each `worktree ` entry, skip the main checkout, then require the basename to start with `<repoName>-` and the suffix to parse as a `semantic` session-id via `parseSessionId()` (UUID / random suffixes excluded). Each match yields `{ wtPath, sessionId, branch }`. Any git failure → `[]` (conservative no-op). Git invocation is via the injection-safe `opts.execFileFn` (default `execFileSync` with an args array — #577 HARDEN-001).

### Staleness check

A worktree is stale iff `mtime(worktree-dir) < now - stale-branch-days × 86400 × 1000`. Read `stale-branch-days` from Session Config (default 7):

> **Authoritative impl:** `scripts/lib/memory-cleanup/worktree-sweep.mjs` — `isWorktreeStale(wtPath, staleBranchDays)`. Import and call; do NOT re-implement from this doc.
>
> Algorithm: `statSync(wtPath)`; stale iff `Date.now() - stat.mtimeMs > staleBranchDays × 24 × 60 × 60 × 1000`. A missing or unreadable path → `false` (conservative no-op).

### Integration with the existing housekeeping prune AUQ

After Phase 4 (Prune & Index) compiles its list of items to offer for removal, ALSO include any stale auto-promoted worktrees. The user sees them in the same AUQ ("batch-decide" per PRD §3 P3 Gherkin row 4):

```js
import { execFileSync } from 'node:child_process';
import { listAutoPromotedWorktrees, isWorktreeStale } from '$PLUGIN_ROOT/scripts/lib/memory-cleanup/worktree-sweep.mjs';
import { discoverActiveSessions } from '$PLUGIN_ROOT/scripts/lib/session-discovery.mjs';

const staleBranchDays = $CONFIG['stale-branch-days'] ?? 7;
const candidates = listAutoPromotedWorktrees(process.cwd(), mainCheckoutRoot);
const stale = candidates.filter((c) => isWorktreeStale(c.wtPath, staleBranchDays));

if (stale.length === 0) {
  // Silent no-op — no stale worktrees to offer.
} else {
  // #580-HARDEN-002: cross-check candidates against LIVE peer sessions before offering removal.
  // A stale-by-mtime worktree may still be the checkout of an active parallel session — removing
  // it would disrupt that session (PSA-002 overlap). Flag any such candidate so the AUQ can warn.
  const active = await discoverActiveSessions(mainCheckoutRoot);
  const livePaths = new Set(active.map((s) => s.worktreePath));
  const annotated = stale.map((wt) => ({ ...wt, activePeer: livePaths.has(wt.wtPath) }));

  // Add to the existing housekeeping prune AUQ. Each stale worktree becomes one option line:
  // Format: `[ ] Stale auto-promoted worktree: <basename> (age <N>d) — remove via 'git worktree remove --force'`
  // If `activePeer` is true, prefix the option with "⚠ ACTIVE PEER SESSION" and make Behalten the default.
  //
  // If memory-cleanup currently presents per-item AUQs (one question per prune candidate),
  // append one question per stale worktree.
  //
  // If memory-cleanup uses a single multiSelect AUQ for the whole batch,
  // add stale worktrees as additional options.
  //
  // Operator selects which to remove; coordinator runs (arg-array, no shell — #577 HARDEN-001):
  //   execFileSync('git', ['-C', mainCheckoutRoot, 'worktree', 'remove', '--force', wtPath])
  // for each selected. WARN line per removal.
}
```

### AUQ example (per-item)

When the candidate's `wtPath` matches a LIVE peer session (`wt.activePeer === true`, from `discoverActiveSessions()` above), the AUQ MUST surface a `⚠ ACTIVE PEER SESSION` warning and keep `Behalten` as the safe default — removing a live session's worktree mid-flight is a PSA-002 overlap that can corrupt another session's working state.

```js
const peerWarning = wt.activePeer
  ? ' ⚠ ACTIVE PEER SESSION — removing may disrupt a live session.'
  : '';

AskUserQuestion({
  questions: [{
    question: `Stale auto-promoted worktree found: ${path.basename(wt.wtPath)} (age ${ageDays}d, branch=${wt.branch}).${peerWarning} Remove?`,
    header: "Stale-Worktree",
    multiSelect: false,
    options: [
      {
        label: "Behalten (Recommended)",
        description: wt.activePeer
          ? "Keep this worktree — a LIVE peer session is using it. Removal would disrupt the active session."
          : "Keep this worktree. Re-evaluate at next /memory-cleanup run.",
      },
      {
        label: "Entfernen",
        description: wt.activePeer
          ? `⚠ ACTIVE PEER SESSION detected. Only choose this if you have confirmed no live session needs it, then run 'git worktree remove --force ${wt.wtPath}'.`
          : `Run 'git worktree remove --force ${wt.wtPath}'.`,
      },
    ],
  }],
});
```

### PSA-003 compliance

Per `.claude/rules/parallel-sessions.md` PSA-003: every `git worktree remove` is destructive — operator must explicitly authorize. The AUQ above satisfies this. Never auto-remove without user confirmation, even for stale worktrees. The `--force` flag is acceptable here only because the AUQ already secured explicit per-worktree consent; never apply `--force` to worktrees the operator did not select.

### Cross-references

- PRD: "Parallel-Aware Sessions" (#568; archived in the private Meta-Vault) §3 P3 Gherkin row 4 + §3.A P3 EARS state-driven clause
- `stale-branch-days` config: `scripts/lib/config.mjs:138` (default: 7)
- Detection helper: `parseSessionId()` from `scripts/lib/session-id.mjs`
- Stale-sweep helpers: `listAutoPromotedWorktrees()` + `isWorktreeStale()` from `scripts/lib/memory-cleanup/worktree-sweep.mjs`
- Live-peer detection (#580-HARDEN-002): `discoverActiveSessions(repoRoot)` from `scripts/lib/session-discovery.mjs` — flags stale candidates whose `wtPath` matches an active session so the AUQ warns before removal
- PSA-003: `.claude/rules/parallel-sessions.md`

## Output

After completing all four phases, report:

- Files created / updated / deleted (paths only — no full diffs in the chat output).
- `MEMORY.md` line count (before → after).
- Contradictions resolved (with one-line summary each).
- Stale entries pruned (count + categories).
- Any issues that need manual attention (e.g. ambiguous facts that need user input — surface via `AskUserQuestion` rather than guessing).

### Session-End Signal: "cleanup ran this session" (#699)

**A completed cleanup — including a healthy no-op where MEMORY.md was already healthy and no files were mutated — counts as a cleanup run.** The session-end skill MUST stamp `memory_cleanup_at` on the session record whenever `/memory-cleanup` ran in THIS session, regardless of outcome (dry-run, apply-pending, or no-op).

This advances the auto-dream cadence marker (`readDreamSignals` → `lastCleanupAt` in `scripts/lib/auto-dream.mjs`) so `shouldDispatchAutoDream` does not fire a false nudge on the next session.

**Signalling contract (coordinator responsibility at session-end Phase 3.7):**
- Set `ranMemoryCleanupThisSession = true` when `/memory-cleanup` ran this session in ANY mode or with ANY outcome.
- Pass this flag to `stampMemoryCleanup()` from `scripts/lib/memory-cleanup-stamp.mjs` before emitting the session record (see `skills/session-end/session-metrics-write.md` § 1-pre).
- Do NOT distinguish between "applied changes" and "healthy no-op" — both count.
- Do NOT set `memory_cleanup_at` to `null`; simply omit the field when cleanup did not run.

## Anti-Patterns

- **Don't rewrite memory you don't understand.** If a fact's provenance is unclear, leave it and flag it in the output instead of deleting.
- **Don't bulk-delete on the first run.** Cleanup runs are cheap; aggressive pruning costs context that can't easily be reconstructed.
- **Don't create new memory types.** The four-type taxonomy (`user`, `feedback`, `project`, `reference`) is load-bearing for the relevance heuristic.
- **Don't touch `MEMORY.md` if line-count is already healthy.** Re-ordering for its own sake creates churn without value.
