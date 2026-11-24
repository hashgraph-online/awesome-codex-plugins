---
name: choosing-between-options
description: Use when a decision is the user's to make (which option, which target, go or stop), when a request reads two ways, when a question has a handful of answers rather than a conversation, or when the user is watching the board rather than the chat. Asks on the stickypane board with a form that has buttons, waits for the press, and reads the answer back.
metadata:
  cases: form-F5 html-H1
---

# Choosing between options

```sh
stickypane note write cache-way --open <<'EOF'
---
type: form
title: Which cache invalidation?
---
"Clear the cache on update" reads two ways.

## Strategy
- ( ) delete the key on every write
  Simple; the next read is slow.
- ( ) bump a version in the key
  No slow read; old keys expire on their own.

## Other
>

[ Use this ] [ Neither ]
EOF
stickypane wait cache-way --timeout 10m    # always with a limit
```

Shapes: form; html beside it when the options need a table to compare.
How to word each line: `${CLAUDE_PLUGIN_ROOT}/rules/writing-notes.md`.

`wait` prints one line per question:

```
submitted: Use this
at: 2026-10-02T14:03:05+09:00
Strategy: bump a version in the key
Other: -
```

`--json` gives `{"submitted":true,"button":"Use this","at":"...","answers":[...]}`.
Exit code 3: the time ran out and nothing is printed. Exit code 1: the
note is not a form or is not there. `stickypane answers cache-way` prints
the same now, without waiting (`submitted: no` until a button is pressed).
A form that keeps its `submitted` keys answers at once with the old
choice: to ask again, write the form again without them.

## How

- Ask only what you cannot decide yourself, and only once. One question,
  or a few that belong together, per form; a question is a heading with
  its options under it, each with one line on what it costs.
- Leave a `>` line for an answer you did not list.
- When the options need a comparison (numbers, several criteria), write
  it as a page, `stickypane note show compare.html`, and keep the form for
  the choice. The terminal shows the page's text only.
- Report the answer in one line, then act on it.
- When the time runs out, say so and ask in the chat, or go on with what
  does not depend on it. Never guess the answer.
- An answer that is a sentence: `talking-while-working`. An action hard to
  undo: `approving-a-risky-action`.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/preferences-up-front.md`: collect the user's choices once, before a task starts.
- `references/recording-the-decision.md`: keep what was decided and why, after the user chose.
