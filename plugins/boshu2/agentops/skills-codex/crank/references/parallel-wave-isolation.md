# Parallel-Wave Isolation (wave size ≥ 2)

## Problem

When `/crank` dispatches 2+ parallel workers in a shared clone, sibling workers can clobber each other's staged files. The proximate cause is `git checkout` mutating the shared working tree mid-task — worker A stages files, worker B runs `git checkout` to switch to its branch, worker A's stage is gone.

Observed 2026-04-30 (soc-lrwk crank): 2 of 3 parallel workers lost staged work and recovered via stash + ephemeral worktrees, costing ~30% wall-time per affected worker.

## Why three tiers, not just "always use worktrees"

The user already invested in worktree-sprawl prevention:
- Commit `83bea6bd` enforces canonical-root worktree hygiene.
- `scripts/check-worktree-disposition.sh` flags stray worktrees in CI.
- `git worktree prune` cleans up stale ones.
- AGENTS.md documents the policy.

Defaulting to per-worker worktrees regresses that investment. The right answer is conditional escalation, gated on the actual signal (`scripts/preflight-swarm.sh`).

Council brainstorm + judge verdicts: `.agents/council/2026-04-30-brainstorm-crank-parallel-wave.md`.

## Tier 1 — Branch isolation prompt rule (every parallel wave ≥ 2)

Inject this rule verbatim at the top of every worker's `spawn_agent(message=...)` text, before the issue body:

```
WORKER GIT DISCIPLINE (parallel wave — read first):
- Your first git op is: git checkout -b feat/<epic-id>-<task-slug> origin/main
- You MUST NOT run any of these on the shared working tree:
  - git checkout <existing-branch>
  - git switch
  - git stash pop
  - git reset --hard
- Stay on your branch for the entire task. To inspect another branch's
  content, use: git show <branch>:<path> (read-only, no checkout).
```

This is the load-bearing default. It prevents the proximate failure (sibling worker's `git checkout` mutates your staged files in the shared tree) at zero infrastructure cost. Workers' tooling (`gh pr merge`, `git stash pop` in recovery flows, etc.) is the typical violator — the rule must be in-context, not just in doctrine.

## Tier 2 — Pre-flight + conditional escalation to ephemeral worktrees

Before spawning workers, run:

```bash
bash scripts/preflight-swarm.sh "$WAVE_TASK_FILES" || PREFLIGHT_RC=$?
```

- **Exit 0:** Tier 1 alone is sufficient. Spawn workers in the shared clone.
- **Non-zero (conflict risk detected):** Escalate this wave to per-worker ephemeral worktrees per [worktree-per-worker.md](worktree-per-worker.md):

  ```bash
  for task in $WAVE_TASKS; do
      worktree="${REPO_ROOT}-worktrees/wave-${wave}-${task}"
      git worktree add "$worktree" -b "feat/<epic>-${task}" origin/main
      # Inject "WORKING DIRECTORY: $worktree" into the worker prompt
  done
  ```

  Workers in escalated mode operate in their own worktree. Orchestrator removes the worktree at wave-end after the worker's commit + push lands:

  ```bash
  for task in $WAVE_TASKS; do
      git worktree remove "${REPO_ROOT}-worktrees/wave-${wave}-${task}"
  done
  ```

The escalation criterion is **owned by `preflight-swarm.sh`**, not duplicated here. Tune heuristics there if needed.

## Tier 3 — Wave-end disposition gate

After every wave (Tier 1 OR Tier 2), run:

```bash
bash scripts/check-worktree-disposition.sh
```

This catches stragglers — worktrees that should have been removed but weren't. **The script is a blocking gate**: it exits non-zero on *any* unexpected branch-attached worktree, dirty canonical-root status, or missing preserved ref. The orchestrator MUST treat a non-zero exit as a wave failure and surface the flagged worktrees in the wave summary before halting. There is no "advisory" or ">N stragglers" threshold — zero tolerance.

## Why this layering

| Tier | Cost | Fires When | Solves |
|---|---|---|---|
| 1 | $0 (prompt only) | Every parallel wave ≥ 2 | Sibling-worker `git checkout` clobber (the proximate failure) |
| 2 | One worktree per worker, ephemeral | `preflight-swarm.sh` flags overlap | Same-file collisions, generated-artifact races |
| 3 | One script call | Every wave-end | Sprawl regression — leftover worktrees |

Reuses existing tooling: `scripts/preflight-swarm.sh`, `scripts/check-worktree-disposition.sh`, [worktree-per-worker.md](worktree-per-worker.md), `git worktree prune`. No new scripts.

## See Also

- [worktree-per-worker.md](worktree-per-worker.md) — when ephemeral per-worker worktrees ARE warranted (the "USE/DON'T USE" matrix Tier 2 routes through)
- `.agents/learnings/2026-04-30-branch-isolation-for-multi-session-crank.md` — branch-isolation pattern that Tier 1 codifies
- `.agents/council/2026-04-30-brainstorm-crank-parallel-wave.md` — full council judgment behind this design
