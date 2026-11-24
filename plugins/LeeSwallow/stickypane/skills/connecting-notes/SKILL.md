---
name: connecting-notes
description: Use when one note should point to, show, count or react to another: a link between notes, a summary that shows other notes inside it, a chart that counts a checklist or a board, or waiting for the user to tick, move, send or press. Uses [[links]], ![[embeds]], from charts and stickypane watch.
metadata:
  cases: note-N8 checklist-C4
---

# Connecting notes

```sh
# a summary that shows the live notes inside it, each kept in one place
stickypane note write status --open <<'EOF'
---
title: Where the release stands
---
![[plan]]
![[progress]]
Open question: [[cache-way]].
EOF
# a step only the user can do: wait for their tick, with a limit
stickypane todo add plan "user: rotate the production key"
stickypane watch --once --note plan --type item.ticked --timeout 30m --json
stickypane index        # each note, with ← N for the notes that link to it
```

Shapes: any; these are ways for notes to meet, from the lightest:

| Want | Write | The board |
| --- | --- | --- |
| point to a note | `[[plan]]`, `[[plan#tests]]`, `[[deploy/run\|the run]]` | draws the name; `f` follows it; the index counts backlinks |
| show it here | a line that is only `![[plan]]` | draws that note there, in its own shape, read only |
| count it | `from: plan` in a chart's front matter | writes the numbers: done and open, cards per column, answers, lines |
| react to it | `stickypane watch ... --exec CMD` | runs CMD in the user's shell for each event |

With one source a chart counts it by its shape; with several, one line per
note (percent done, cards, answers or lines).

## Waiting and reacting

`watch --once` ends at the first matching event and prints it; exit code
3 means the time ran out. Start the step that needs it only after the
event, not on a guess that the user did it.

```sh
stickypane watch --note plan --type item.ticked --exec 'stickypane chart add progress done 1'
stickypane watch --type card.moved --exec '[ "$STICKY_TO" = Done ] && printf "\a"'
```

The command gets the event in `STICKY_EVENT` (JSON) and in `STICKY_NOTE`,
`STICKY_TYPE`, `STICKY_ITEM`, `STICKY_FROM` and `STICKY_TO`. Events:
note.created, note.changed, note.removed, item.added, item.ticked,
item.unticked, card.added, card.moved, form.submitted, log.appended,
chart.changed, message.added.

## Rules

- Prefer the lightest way: a link before an embed, `from:` before a watch.
- A summary embeds the notes; it does not copy them. The source stays one.
- A watch with `--exec` keeps running and acts for the user: start it in
  the background, and say how to stop it.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.
