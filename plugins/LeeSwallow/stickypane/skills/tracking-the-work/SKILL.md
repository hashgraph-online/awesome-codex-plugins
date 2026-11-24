---
name: tracking-the-work
description: Use when a task has more than a few steps, when it will take long enough that the user may look away, and whenever the user asks "where are we". Keeps the work visible on the stickypane board, as a checklist or kanban for the steps and a log for what happened, updated as you go.
metadata:
  cases: checklist-C1 checklist-C2 log-L1
---

# Tracking the work

```sh
# before the first change: the plan, one step a line
stickypane todo add refactor "find every caller"     # makes refactor.md, open
stickypane todo add refactor "move the function"
stickypane todo add refactor "run the tests"
stickypane todo add worktrees/feat-chart/todo "fix the axis"   # in a worktree

# while working: tick a step once it is done, log what happened
stickypane todo check refactor callers               # a part of the text, or #1
stickypane log add worklog --time "14 callers found, 2 in tests"
stickypane todo check refactor "move"

# the end: the last tick and the outcome in one line
stickypane todo check refactor "run the tests"
stickypane log add worklog --time "refactor done: 14 files, tests green"
```

Shapes: checklist for the steps; board when the steps move through
columns (`stickypane card add work "login API" --to "To do"`, then
`stickypane card move work login --to Done`); log for what happened.

Each command prints where the note stands (`refactor.md: 2/3`); report
that line. The board writes the time of each tick (`✅ 14:02`) and of each
log line.

## Rules

- Put the steps on the board before you change code, so the user sees
  the plan while it can still change.
- Tick a step when it is done and you have seen it done (the test passed,
  the file is there), not when you start it.
- A step is a line a reader understands without the chat: "move the
  function", not "step 2".
- One log line is one event, with the number that matters.
- Leave the finished note where it is: it is the record.
- A decision that is the user's: `choosing-between-options`. Telling the
  user something as you go: `talking-while-working`. A chart of how far
  along it is: `showing-numbers`. Picking up this note in a later session:
  `resuming-and-handing-off`.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/when-the-plan-changes.md`: a step is no longer right.
- `references/parallel-subagents.md`: several agents work at once and meet at the end.
- `references/lanes-for-agents.md`: a kanban that shows which agent holds which card.
