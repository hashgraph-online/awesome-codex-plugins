---
name: asking-the-user
description: Use when a decision is the user's to make (which option, which target, go or stop), when a question has a handful of answers rather than a conversation, or when the user is watching the board rather than the chat. Asks on the stickypane board with a form that has buttons, waits for the press, and reads the answer back.
---

# Asking the user on the board

```sh
# 1. write .sticky/deploy.md (below), then
stickypane show deploy
# 2. wait for a button, always with a limit
stickypane wait deploy --timeout 10m
```

The form:

```markdown
---
type: form
title: Deploy now?
---
The build is green. Where should it go?

## Target
- ( ) staging
  Try it there first.
- ( ) production

## Also
- [ ] run migrations

## Note
>

[ Deploy ] [ Cancel ]
```

| Line | Is |
| --- | --- |
| `- ( ) text` | one choice among the options under the same heading |
| `- [ ] text` | any number of choices |
| indented line under an option | what choosing it means |
| `> ` | a line the user types into |
| `[ Label ] [ Label ]` | the buttons; a form without any gets `[ Submit ]` |

`wait` prints one line per question:

```
submitted: Deploy
at: 2026-10-02T14:03:05+09:00
Target: production
Also: run migrations
Note: after lunch
```

`--json` gives `{"submitted":true,"button":"Deploy","answers":[...]}`. Exit
code 3: the time ran out and nothing is printed. Exit code 1: the note is
not a form or is not there. `stickypane answers deploy` prints the same now,
without waiting (`submitted: no` until a button is pressed).

Report the answer in one line; acting on it is the caller's job. Then
`stickypane hide deploy`, or leave the form as the record of the decision.

## Rules

- Ask only what you cannot decide yourself, and only once.
- One question, or a few that belong together, per form. A question is a
  heading with its options under it.
- Name buttons by what they do (`[ Deploy ] [ Cancel ]`), never `[ OK ]`.
- When the time runs out, say so and take the safe path or ask in chat.
  Never guess the answer.
- To ask again, write the form without the `submitted` keys; a form that
  still has them answers at once with the old choice.
- An answer that is a sentence, or a back and forth: `talking-in-chat`.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.
