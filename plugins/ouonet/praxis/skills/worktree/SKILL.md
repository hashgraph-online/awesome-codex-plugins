---
name: worktree
description: Use for non-trivial or parallel work that should happen in a separate git worktree.
---
# Worktree

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`. Treat each repository as an independent Git and worktree boundary; never run a workspace-wide Git mutation from their common parent.

Before creating worktrees, resolve each registered repository and verify status and baseline. Map paths in the coordinator plan and use the change-set ID in names. A missing repo, unrelated dirty change, or red baseline blocks the change. Detached HEAD is allowed for read-only integration, not implementation. Do not clone or clean automatically.

```bash
git worktree add ../<repo>-<topic> -b <type>/<topic>   # <type>: feat | fix | chore | ...
cd ../<repo>-<topic> && <setup> && <run tests>
```

Baseline must be green in every participating repository. If red, STOP - don't build on broken ground. Done → `ship`.

## Tool scope

Worktrees are separate directories from the main repo. Semantic indexing (code graph, symbol search) covers the original repo, not the worktree. File tools (`read`, `grep`, `glob`) work normally. For short-lived worktrees this is acceptable; for long sessions, note this limitation to the agent at dispatch.
