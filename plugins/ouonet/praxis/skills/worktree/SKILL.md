---
name: worktree
description: Use for non-trivial or parallel work that should happen in a separate git worktree.
---
# Worktree

```bash
git worktree add ../<repo>-<topic> -b <topic>
cd ../<repo>-<topic> && <setup> && <run tests>
```

Baseline must be green. If red, STOP - don't build on broken ground. Done -> `ship`.