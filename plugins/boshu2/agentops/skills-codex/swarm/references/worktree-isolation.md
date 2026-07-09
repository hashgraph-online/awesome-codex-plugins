# Worktree Isolation (Multi-Epic Dispatch)

**Default behavior:** Auto-detect and prefer runtime-native isolation first.

The Codex runtime has no native per-agent worktree isolation: for write-heavy parallel waves, create a `git worktree` per subagent and run `codex exec -C <worktree>`, or give each ATM/NTM swarm pane its own worktree. Use the manual `git worktree` fallback below.

## Isolation Semantics Per Spawn Backend

| Backend | Isolation Mechanism | How It Works |
|---------|-------------------|--------------|
| **Codex subagents** (`codex exec -C <dir>`) | manual `git worktree` per subagent | Create a worktree per parallel subagent and run `codex exec -C <worktree>`; changes stay isolated from other agents and the main tree until merged |
| **ATM / NTM swarm panes** | one `git worktree` per pane | Each pane operates in its own worktree; ownership and reservations are coordinated via Agent Mail to avoid collisions |
| **Inline** (no spawn) | None | Operates directly on the main working tree; no isolation possible |

**Sparse checkout for large repos:** Set `worktree.sparsePaths` in project settings to limit worktree checkouts to relevant directories. This reduces clone time and disk usage for monorepos where workers only need a subset of the tree.

## Effort Levels for Workers

Use the effort command to right-size model reasoning per worker role:

| Worker Role | Recommended Effort | Rationale |
|-------------|-------------------|-----------|
| Research/exploration | `low` | Fast, broad scanning — depth not needed |
| Implementation (code) | `high` | Deep reasoning for correct implementation |
| Docs/chore | `low` | Fast execution for simple tasks |

**Key diagnostic:** Codex has no native per-agent isolation — isolation exists ONLY if you created a `git worktree` for the subagent/pane. If a worker's changes appear in the main working tree, no worktree was used; that is the silent-failure mode to guard against.

## Post-Spawn Isolation Verification

After spawning workers, the lead MUST verify each is operating in its own worktree:

1. **`git worktree list`** — one path per active worker; the main checkout must be untouched by worker writes.
2. **`git -C <worktree> status`** — confirms each worker's changes are isolated in its worktree, not the main tree.
3. **If a worker was NOT given a worktree** (changes landed in the main tree):
   - **For waves with 2+ workers touching overlapping files:** abort the wave, fall back to serial execution to prevent conflicts.
   - **For waves with fully independent file sets:** may proceed with caution, but monitor for conflicts.
4. **If you cannot reliably isolate:** create worktrees manually (see below) or switch to serial inline execution.

**When to use worktrees:** Activate worktree isolation when:
- Dispatching workers across **multiple epics** (each epic touches different packages)
- Wave has **>3 workers touching overlapping files** (detected via `git diff --name-only`)
- Tasks span **independent branches** that shouldn't cross-contaminate

Evidence: 4 parallel agents in shared worktree produced 1 build break and 1 algorithm duplication (see `.agents/evolve/dispatch-comparison.md`). Worktree isolation prevents collisions by construction.

## Detection: Do I Need Worktrees?

```bash
# Heuristic: multi-epic = worktrees needed
# Single epic with independent files = shared worktree OK

# Check if tasks span multiple epics
# e.g., task subjects contain different epic IDs (ol-527, ol-531, ...)
# If yes: use worktrees
# If no: proceed with default shared worktree
```

## Creation: One Worktree Per Epic

Before spawning workers, create an isolated worktree per epic:

```bash
# For each epic ID in the wave:
git worktree add /tmp/swarm-<epic-id> -b swarm/<epic-id>
```

Example for 3 epics:
```bash
git worktree add /tmp/swarm-ol-527 -b swarm/ol-527
git worktree add /tmp/swarm-ol-531 -b swarm/ol-531
git worktree add /tmp/swarm-ol-535 -b swarm/ol-535
```

Each worktree starts at HEAD of current branch. The worker branch (`swarm/<epic-id>`) is ephemeral — deleted after merge.

## Worker Routing: Inject Worktree Path

Pass the worktree path as the working directory in each worker prompt:

```
WORKING DIRECTORY: /tmp/swarm-<epic-id>

All file reads, writes, and edits MUST use paths rooted at /tmp/swarm-<epic-id>.
Do NOT operate on /path/to/main/repo directly.
```

Workers run in isolation — changes in one worktree cannot conflict with another.

**Result file path:** Workers still write results to the main repo's `.agents/swarm/results/`:
```bash
# Worker writes to main repo result path (not the worktree)
RESULT_DIR=/path/to/main/repo/.agents/swarm/results
```

The orchestrator path for `.agents/swarm/results/` is always the main repo, not the worktree.

## Merge-Back: After Validation

After a worker's task passes validation, merge the worktree branch back to main:

```bash
# From the main repo (not worktree)
git merge --no-ff swarm/<epic-id> -m "chore: merge swarm/<epic-id> (epic <epic-id>)"
```

Merge order: respect task dependencies. If epic B blocked by epic A, merge A before B.

**Base-SHA ancestry check before merge-back:** Worktree branches rooted off non-main commits pull unintended branch ancestry during `git merge --no-ff`, causing extra files to land. Before merging:
- **Single-commit worktree branches:** Prefer `git cherry-pick <sha>` over `git merge --no-ff`. Cherry-pick applies only the commit's diff and avoids pulling unintended ancestry.
- **Multi-commit worktree branches:** Run `git rebase main swarm/<epic-id>` before `git merge --no-ff` to re-root the branch onto current main HEAD and eliminate stale ancestry.

**Merge Arbiter Protocol:**

Replace manual conflict resolution with a structured sequential rebase:

1. **Merge order:** Dependency-sorted (leaves first), then by task ID for ties
2. **Sequential rebase** (one branch at a time):
   ```bash
   # For each branch in merge order:
   git rebase main swarm/<epic-id>
   ```
3. **On rebase conflict:**
   - Check the file-ownership map from Step 1.5
   - If the conflicting file has a single owner → use that owner's version
   - If the conflicting file has multiple owners → use the version from the task being merged (current branch)
   - Run tests after resolution to verify
4. **If tests fail after conflict resolution:**
   - Spawn a fix-up worker scoped ONLY to the conflicting files
   - Worker receives: both versions, test output, ownership context
   - Max 3 fix-up retries per conflict
   - If still failing after 3 retries → abort merge for this branch, escalate to human
5. **Display merge status table** after all merges complete:
   ```
   Merge Status:
   ┌────────────────────┬──────────┬────────────┬───────────┐
   │ Branch             │ Status   │ Conflicts  │ Fix-ups   │
   ├────────────────────┼──────────┼────────────┼───────────┤
   │ swarm/task-1       │ MERGED   │ 0          │ 0         │
   │ swarm/task-2       │ MERGED   │ 1 (auto)   │ 0         │
   │ swarm/task-3       │ MERGED   │ 1 (fixup)  │ 1         │
   └────────────────────┴──────────┴────────────┴───────────┘
   ```

Workers must not merge — lead-only commit policy still applies.

## Cleanup: Remove Worktrees After Merge

```bash
# After successful merge:
git worktree remove /tmp/swarm-<epic-id>
git branch -d swarm/<epic-id>
```

Run cleanup even on partial failures (same reaper pattern as team cleanup).

## Full Pre-Spawn Sequence (Worktree Mode)

```
1. Detect: does this wave need worktrees? (multi-epic or file overlap)
2. For each epic:
   a. git worktree add /tmp/swarm-<epic-id> -b swarm/<epic-id>
3. Spawn workers with worktree path injected into prompt
4. Wait for completion (same as shared mode)
5. Validate each worker's changes (run tests inside worktree)
6. For each passing epic:
   a. git merge --no-ff swarm/<epic-id>
   b. git worktree remove /tmp/swarm-<epic-id>
   c. git branch -d swarm/<epic-id>
7. Commit all merged changes (team lead, sole committer)
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--worktrees` | Force worktree isolation for this wave | Off (auto-detect) |
| `--no-worktrees` | Force shared worktree even for multi-epic | Off |
