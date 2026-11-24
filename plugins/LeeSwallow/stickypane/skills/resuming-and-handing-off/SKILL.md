---
name: resuming-and-handing-off
description: Use when a session starts from what an earlier one left on the stickypane board, or ends while the work goes on, so the next session (yours, another agent's, or the user's) knows where it stands without the chat.
metadata:
  cases: checklist-C8 log-L7
---

# Resuming and handing off

```sh
# starting: read what is there before you do anything
stickypane index                     # every note, with where it stands
stickypane note cat refactor         # the steps: ticked is done, unticked is not
stickypane note cat handoff          # the last session's note to you

# ending: one line on where it stands and what comes next
stickypane log add handoff --time "branch feat/cache: steps 1-3 done; next: run e2e (needs the browsers); open question in [[cache-way]]"
```

Shapes: checklist for what is done and what is not; log for the
hand-off lines; board when the next one takes cards.

The board is files: it outlives the session that wrote it. A checklist
is the checkpoint, and the hand-off log says what the checklist cannot.

## How

- Resuming: read the index, the checklist and the last hand-off line
  first. Go on from the first unticked step; do not redo a ticked one
  without a reason you can name.
- If a ticked step looks undone (the test fails now), untick it and say
  why: `stickypane todo uncheck refactor "run the tests"`.
- Ending: one hand-off line with the branch, what is done, the next
  step, and anything open, linked by name. Keep it to the facts the next
  session cannot read off the checklist.
- Do not hand off in the chat only: a chat message scrolls away, the
  log stays.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/handing-a-card-on.md`: pass a card to another agent with what it needs.
