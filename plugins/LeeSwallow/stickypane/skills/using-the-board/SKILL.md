---
name: using-the-board
description: Use when the user asks to show, track, list, chart, draw or explain something "on the board", when something is better seen than read in chat, and before saying what the board shows. The way in to the stickypane board (a terminal pane next to you): the everyday commands, and which skill to follow for a bigger job.
---

# Using the board

```sh
stickypane index                         # every note in a line: what it is, where it stands
stickypane show README.md                # any file of the project, onto the board
stickypane todo plan add "write tests"   # one thing changes: one command
```

The board is the project's `.sticky/` folder; one file is one note. Every
command prints one line saying where the note stands (`plan.md: 0/3`):
report it, do not read the file back. A missing note is made, and so is a
missing board in a git repository.

## Which skill

| The job | Follow |
| --- | --- |
| a task of several steps the user follows | `tracking-progress` |
| a decision that is the user's: which, go or stop | `asking-the-user` |
| talking back and forth on the board while you work | `talking-in-chat` |
| one note that counts, shows or answers another | `connecting-notes` |

Anything else is one of the commands below.

## One thing changes

```sh
stickypane todo plan check tests               # plan.md: 1/3   (add, uncheck)
stickypane card work move login --to Done      # work.md: 4 cards   (add "text" --to Doing)
stickypane chart tokens add input 1200         # tokens.md: input = 6200   (set)
stickypane log worklog --time "tests passed"   # worklog.md: 12 lines
stickypane say chat "41/41 pass" --as claude   # chat.md: 3 messages
stickypane set plan title="The plan" open=true size=half
stickypane show plan; stickypane hide plan     # on the screen, or folded away
stickypane mv plan deploy/                     # into the tab deploy (rm, restore)
```

An item, a card or a column is named by its text, a part of it that nothing
else has, or its position (`#2`). When a name fits nothing or more than one
thing, the error lists what there is: pick from it.

## A shape of its own

Write the file into `.sticky/` with `open: true` in its front matter.

| Shape | Front matter | Body |
| --- | --- | --- |
| note | none | any Markdown; a `mermaid` block is drawn |
| board | `type: board` | `## Column`, then `- card` lines |
| checklist | `type: checklist` | `- [ ]` and `- [x]` lines |
| log | `type: log`, or a `.log` file | one line per entry |
| chat | `type: chat` | `@name HH:MM text` under `## YYYY-MM-DD` |
| chart | `type: chart`, `view: bar\|spark\|heat` | `label: number` lines |
| form | `type: form` | the `asking-the-user` skill |
| script | a `.sh` file | shell; the user runs it after a yes |

Each shape in a paragraph: `references/kinds.md`. A full example:
`stickypane kinds <shape>`.

## Reading

`stickypane index` answers "what is on the board". `stickypane cat <name>`
prints one note, `stickypane answers <form>` what the user chose, and
`stickypane watch --once --note <name>` waits for the user to do something.

## Rules

- Prefer, in order: `show`, a one-line command, writing a file.
- Run `stickypane cat <name>` before rewriting a note: the user edits from
  the board. The one-line commands never overwrite.
- One note per thing the user follows; show what to read now, fold the rest.
- What the board writes itself, and what is the user's:
  `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md`. How to word a note:
  `${CLAUDE_PLUGIN_ROOT}/rules/writing-notes.md`.
