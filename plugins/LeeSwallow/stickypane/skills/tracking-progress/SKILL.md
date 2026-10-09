---
name: tracking-progress
description: Use when a task has more than a few steps, when it will take long enough that the user may look away, and whenever the user asks "where are we". Keeps the progress of the work visible on the stickypane board, as a checklist or kanban for the steps and a log for what happened, updated as you go.
---

# Tracking progress on the board

```sh
# start: one note for the task (a checklist, or a kanban when it has columns)
stickypane todo refactor add "find every caller"     # makes refactor.md, open
stickypane todo refactor add "move the function"
stickypane card work add "login API" --to "To do"

# while working
stickypane todo refactor check callers               # a part of the text, or #1
stickypane card work move login --to Done
stickypane log worklog --time "tests passed, 3 flaky left"
stickypane chart tokens add input 1200

# finish: tick the last item and log the outcome
stickypane todo refactor check "move"
stickypane log worklog --time "refactor done: 14 files, tests green"
```

Each command prints where the note stands (`refactor.md: 2/3`). Report
that; do not read the note.

## Rules

- One note per task the user follows. Update the one that exists; a second
  checklist for the same task is noise.
- Change it with the commands above, never by rewriting the file: the user
  may have ticked or added items from the board.
- A step is a line a reader understands without the chat: "move the
  function", not "step 2".
- Tick an item when it is done, not when you start it.
- Leave the finished note where it is: it is the record. Delete it only
  when the user asks.
- When the work needs the user's decision, use the `asking-the-user` skill;
  to tell the user something as you go, `talking-in-chat`.
- A chart of how far along it is: `connecting-notes` (`from:`), not counts
  you keep yourself.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` and
  `${CLAUDE_PLUGIN_ROOT}/rules/writing-notes.md` apply.
