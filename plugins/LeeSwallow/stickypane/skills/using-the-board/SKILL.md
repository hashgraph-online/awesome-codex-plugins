---
name: using-the-board
description: Use when the user says "on the board", when something is better seen than read in chat, to pick the shape a note takes, and before saying what the board shows. The way in to the stickypane board (a terminal pane next to you): which shape shows what, and which topic to follow.
---

# Using the board

```sh
stickypane index                         # every note in a line: what it is, where it stands
stickypane note show README.md           # any file of the project, onto the board
stickypane todo add plan "write tests"   # one thing changes: one command
```

The board is the project's `.sticky/` folder; one file is one note. Before
the first change, read `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md`:
the commands, and what is the board's to write. To write a note of a shape
of its own, and word it: `${CLAUDE_PLUGIN_ROOT}/rules/writing-notes.md`.

## What to show, in which shape

| To show | Shape | How |
| --- | --- | --- |
| a structure, a flow, an order of calls, a schema | note with a mermaid block | draw it, do not describe it |
| steps, things to do | checklist | `stickypane todo add` |
| work that moves through columns | board | `stickypane card add`, `card move` |
| numbers over time, a distribution, a progress rate | chart | `stickypane chart add`; a rate: `from:` |
| what happened, in order | log | `stickypane log add <name> --time` |
| what the user must choose or approve | form | `stickypane wait` |
| a sentence to the user, or from them | chat | `stickypane chat add` |
| a command the user runs on a yes | script (`name.sh`) | the user presses Run |
| HTTP, WebSocket or gRPC requests and their checks | api (`.http`) | `stickypane api` (experimental) |
| a comparison or a report, read only | html | the terminal shows its text: put the result in a note too |
| writing that runs to many pages | book: a folder in a tab | `stickypane page add` |
| what each worktree changed, and files two of them changed | diff (`type: diff`) | `stickypane diff list` |
| a screen of its own | tab: a folder | `stickypane note mv <name> <tab>/` |

A shape in full, with an example: `stickypane help <shape>`.

## Which topic

| The situation | Follow |
| --- | --- |
| a task of more than a few steps, or "where are we" | `tracking-the-work` |
| the user may write while you work, or the answer is a sentence | `talking-while-working` |
| you explain a structure, a flow or a schema | `drawing-a-diagram` |
| a change that is not small, before the code | `planning-before-code` |
| you are stuck, or there are ways forward to pick from | `reporting-a-blocker` |
| the user must choose, and the options can be listed | `choosing-between-options` |
| an action hard to undo: deploy, delete, push, migrate | `approving-a-risky-action` |
| numbers: test counts, a trend, how far along | `showing-numbers` |
| a command that should run on the user's yes | `handing-over-a-command` |
| proof that an HTTP, WebSocket or gRPC API works | `checking-an-api` |
| a report or a guide of many pages | `reading-long-material` |
| one note that points to, shows, counts or answers another | `connecting-notes` |
| you work in a git worktree | `working-in-a-worktree` |
| a session picks up earlier work, or hands it on | `resuming-and-handing-off` |
| you are done, and the user will come back to check | `finishing-the-task` |

A topic lists its recipes, the cases it covers in full, under `references/`.

## When you need more

- What is on the board: `stickypane index`. One note: `stickypane note cat
  <name>`. What the user chose in a form: `stickypane answers <name>`.
- Wait for the user to do something: `stickypane watch --once --note <name>`.
- Every shape in a paragraph: `references/kinds.md`.

## Recipes

- `references/a-page-a-tool-made.md`: a report a tool already wrote, shown as it is.
