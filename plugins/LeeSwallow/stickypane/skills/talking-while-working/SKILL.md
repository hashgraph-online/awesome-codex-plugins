---
name: talking-while-working
description: Use when the user may send instructions while you work, when the user wants to talk with you on the board instead of in this chat, or when the answer you need is a sentence rather than a choice. Says things in a chat note with stickypane chat add and hears the user's replies as events.
metadata:
  cases: chat-T2 chat-T3 chat-T4
---

# Talking while working

```sh
stickypane chat add chat "starting the migration: 14 files"   # chat.md: 1 message
# between two steps: is there a reply? (does not block)
stickypane watch --once --note chat --type message.added --timeout 1s --json
# a question whose answer is a sentence: wait for it
stickypane chat add chat "which folder holds the legacy handlers?"
stickypane watch --once --note chat --type message.added --timeout 10m --json
```

Shapes: chat. A choice from a handful of answers is a form instead:
`choosing-between-options`.

`chat add` adds `@agent 14:02 starting the migration: 14 files` under
today's heading; the board writes the time. The user answers on the board
with `n`, as themselves. `watch` prints the reply as one JSON line and
ends:

```json
{"type":"message.added","note":"chat.md","item":"skip the legacy folder","from":"min","time":"..."}
```

`item` is what was said and `from` who said it. Exit code 3: the time ran
out with no reply. Over MCP: the `say` tool, then `wait_event` with
`note: chat` and `types: message.added`.

## While you work

- Say three things: what you started, what you found that changes the
  plan, and that you are done. Not every step: steps belong in a
  checklist (`tracking-the-work`).
- Between steps, look for a reply with the 1s `watch` above, and act on
  it as you would on the same words in this chat.
- When a question times out, say so in the chat and go on with what does
  not need the answer. Do not guess it.

## Rules

- One message is one thing, one line.
- Only add with `chat add`; never rewrite `chat.md`. It is the record of
  the conversation, and the user writes to it at the same time.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/changing-direction.md`: the plan changed and the user should know why.
- `references/signing-as-yourself.md`: more than one agent talks in the same chat.
- `references/a-queue-the-user-fills.md`: the user adds work to a checklist while you work.
- `references/the-user-reorders-the-work.md`: the user moves cards to say what comes next.
