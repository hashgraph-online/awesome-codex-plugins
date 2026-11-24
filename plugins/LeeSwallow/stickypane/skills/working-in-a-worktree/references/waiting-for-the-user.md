---
case: worktree-B3
description: Use when you work in a worktree and need the user's answer, while other agents in other worktrees may be waiting too.
---

# Waiting for the user

Shapes: form.

```sh
stickypane note write worktrees/chart/axis-scale --open <<'EOF'
---
type: form
title: chart: log or linear axis?
---
## Axis
- ( ) linear
- ( ) log

[ Use this ]
EOF
stickypane worktree show chart             # forms waiting: 1
stickypane wait worktrees/chart/axis-scale --timeout 10m
```

A form in your book is counted as waiting in `stickypane worktree list`,
so the user sees which agent waits for them. Start the title with your
worktree's name: the user reads many at once.

Done when: `worktree show` counts your form until the user answers it,
and you acted only after `wait` printed the answer.
