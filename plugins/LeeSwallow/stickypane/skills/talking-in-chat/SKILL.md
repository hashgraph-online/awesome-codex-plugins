---
name: talking-in-chat
description: Use when the user wants to talk with you on the board instead of in this chat, when you will work long enough that the user may send instructions meanwhile, or when the answer you need is a sentence rather than a choice. Says things in a chat note with stickypane say and hears the user's replies as events.
---

# Talking in a chat note

```sh
stickypane say chat "starting the migration: 14 files" --as claude   # chat.md: 1 message
stickypane watch --once --note chat --type message.added --timeout 10m --json
```

`say` adds `@claude 14:02 starting the migration: 14 files` under today's
heading; the board writes the time. The user answers on the board with `n`,
as themselves. `watch` prints the reply as one JSON line and ends:

```json
{"type":"message.added","note":"chat.md","item":"skip the legacy folder","from":"min","time":"..."}
```

`item` is what was said and `from` who said it. Exit code 3: the time ran
out with no reply. Over MCP: the `say` tool, then `wait_event` with
`note: chat` and `types: message.added`.

## While you work

- Say what you started, what you found that changes the plan, and when you
  are done. Not every step: progress belongs in a checklist
  (`tracking-progress`).
- Between steps, look for a reply without blocking:
  `stickypane watch --once --note chat --type message.added --timeout 1s`.
- Act on a reply as you would on the same words in this chat.

## Rules

- Say as yourself, with the same `--as` every time.
- One message is one thing, one line. Point to a file with
  `stickypane show <path>` instead of pasting it.
- Only add with `say`; never rewrite `chat.md`. It is the record of the
  conversation, and the user writes to it at the same time.
- A question with a handful of answers is a form: `asking-the-user`.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.
