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

The board is the project's `.sticky/` folder; one file is one note. Before
the first change, read `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md`:
the commands, and what is the board's to write. To write a note of a shape
of its own, and word it: `${CLAUDE_PLUGIN_ROOT}/rules/writing-notes.md`.

## Which skill

| The job | Follow |
| --- | --- |
| a task of several steps the user follows | `tracking-progress` |
| a decision that is the user's: which, go or stop | `asking-the-user` |
| talking back and forth on the board while you work | `talking-in-chat` |
| one note that counts, shows or answers another | `connecting-notes` |

Anything else is one of the commands in the rules.

## When you need more

- One shape in full, with an example: `stickypane help <shape>` (over MCP,
  the guide with the shape as its topic). Every shape in a paragraph:
  `references/kinds.md`.
- What is on the board: `stickypane index`. One note: `stickypane cat
  <name>`. What the user chose in a form: `stickypane answers <name>`.
- Wait for the user to do something: `stickypane watch --once --note <name>`.
