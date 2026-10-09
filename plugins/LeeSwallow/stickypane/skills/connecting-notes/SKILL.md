---
name: connecting-notes
description: Use when one note should point to, show, count or react to another: a link between notes, a note shown inside another, a chart that counts a checklist or a board, or something that should happen when the user ticks, moves, sends or says. Uses [[links]], ![[embeds]], from charts and stickypane watch.
---

# Connecting notes

```sh
stickypane write progress --type chart --open <<'EOF2'
---
from: plan, work
---
EOF2
stickypane index        # each note, with ← N for the notes that link to it
```

The board fills in `progress` from `plan` and `work` and keeps it up to
date in the file. Four ways for notes to meet, from the lightest:

| Want | Write | The board |
| --- | --- | --- |
| point to a note | `[[plan]]`, `[[plan#tests]]`, `[[deploy/run\|the run]]` | draws the name; `f` follows it; the index counts backlinks |
| show it here | a line that is only `![[plan]]` | draws that note there, in its own shape, read only |
| count it | `from: plan` in a chart's front matter | writes the numbers: done and open, cards per column, answers, lines |
| react to it | `stickypane watch ... --exec CMD` | runs CMD in the user's shell for each event |

With one source a chart counts it by its shape; with several, one line per
note (percent done, cards, answers or lines).

## Reacting

```sh
stickypane watch --note plan --type item.ticked --exec 'stickypane chart progress add done 1'
stickypane watch --type card.moved --exec '[ "$STICKY_TO" = Done ] && printf "\a"'
```

The command gets the event in `STICKY_EVENT` (JSON) and in `STICKY_NOTE`,
`STICKY_TYPE`, `STICKY_ITEM`, `STICKY_FROM` and `STICKY_TO`. Events:
note.created, note.changed, note.removed, item.ticked, card.moved,
form.submitted, log.appended, chart.changed, message.added.

## Rules

- Prefer the lightest way: a link before an embed, `from:` before a watch.
- Do not write the values of a `from:` chart; the board rewrites them.
- A watch with `--exec` keeps running and acts for the user: start it only
  when asked, in the background, and say how to stop it.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.
