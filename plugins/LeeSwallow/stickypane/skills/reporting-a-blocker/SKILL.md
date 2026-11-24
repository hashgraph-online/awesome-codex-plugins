---
name: reporting-a-blocker
description: Use when you are stuck (the same failure a third time, a missing access, a question only the user can answer) or the way forward is a choice between ways. Puts what blocks you, what you tried and the ways out in one note on the stickypane board, instead of a long log in the chat.
metadata:
  cases: note-N6
---

# Reporting a blocker

```sh
stickypane note write blocked --open <<'EOF'
---
title: Blocked: the e2e test times out
---
**What fails.** `npm run e2e` times out at login, 3 runs of 3.
**Tried.** A longer timeout (60 s): same. A fresh database: same.
**Last line.** `browserType.launch: Executable doesn't exist` (full output: [[e2e.log]])
**Ways out.**
1. Install the browsers (`npx playwright install`): 400 MB download.
2. Skip e2e here and run it in CI only.
EOF
stickypane chat add chat "blocked on e2e: two ways out on the board, in 'blocked'"
```

Shapes: note for the report; chat for the one line that points to it;
a form when the ways out are the user's choice (`choosing-between-options`).

## How

- Write the note the third time the same thing fails, not the first.
- Four parts: what fails, what you tried, the line that says why, the
  ways out with what each costs.
- The full output goes in a file, linked; the note keeps one line of it.
- While you wait, go on with work the blocker does not touch, and mark
  the blocked step on the checklist.
- When it is unblocked, say how in one line of the note and hide it:
  `stickypane note hide blocked`.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/a-blocked-step.md`: mark the step on the checklist and go around it.
- `references/the-line-that-failed.md`: keep the line that says why, not the whole output.
