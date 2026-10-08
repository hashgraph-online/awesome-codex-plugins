---
name: interactive-fiction
description: This skill should be used when the user asks to "write a branching story", "interactive fiction", "choose your own adventure", "plan the branches", "choice graph", "add a choice", "gamebook", "Twine", "Ink", "draft a branch", "where the branches rejoin", "add an ending", "unreachable chapter", "path continuity", "state-differs-by-path", or wants to plan, draft, or revise a story project whose chapters carry `choices`. NOT for turning a finished linear book into an interactive edition in Ink or Twine (use adaptation).
---

# Interactive Fiction

## Overview

Plan, draft, and revise a branching book: a story project whose chapters
are passages joined by `choices` in their frontmatter. The chapters and
their choices are the source of truth. `story continuity` follows the paths
of choices, and `story build --format twee` or `--format ink` turns the
project into a playable Twine or ink story.

This skill owns books written to branch from the start. Turning an existing
linear book into an interactive edition (a branch map drawn from its scenes,
then a copied project) belongs to the `adaptation` skill; once that edition
project exists, draft and revise its chapters here.

## Prerequisites

A story project with `story.md` in the root. For a new book, start it with
the `story-init` skill first. Read `story.md` (`language`, `pov`, `tense`,
`form`, `status`, `ifid`) and `chapters/_index.md`, then the `choices` of
every chapter: together they are the graph. A small example is
[`examples/the-gull-rock-light`](../../examples/the-gull-rock-light/), a
branch-and-bottleneck story with two endings.

## When to Use

- Planning a choice graph: structure, branch points, rejoins, endings
- Writing or changing `choices` entries
- Drafting a chapter on a branch, at a rejoin, or at an ending
- Revising a branching book, and reading `state-differs-by-path`,
  `unreachable-chapter`, and the other branching findings
- Building the book as Twine or ink
- NOT for converting a linear book (use `adaptation`), drafting a linear
  chapter (use `chapter-writing`), or a linear continuity audit (use
  `revision-continuity`). Prose craft inside a passage still comes from
  `scene-craft` and `line-editing`

## How The Graph Works

- Each chapter is one passage. Its `choices` are where the reader can go:

  ```yaml
  choices:
    - text: Search the rocks for Tobias
      to: chapter-02
    - text: Climb the tower to the lamp
      to: chapter-03
  ```

- The lowest-numbered chapter is the start.
- Once any chapter has `choices`, the links are exactly the choices: a
  chapter with none is an ending, and a chapter that leads on to one place
  needs a single choice (`text: Continue`). With no choices anywhere the
  book is linear again.
- `text` becomes the link text: no `[`, `]`, `|`, `->`, `<-`, or line
  break, and no final `<`. Quote it if it looks like a number.
- `to` is a chapter id. It may be the chapter itself (a loop) or, while
  planning, a `chapter-NN` with no file yet; the builds need every target
  written.

## Workflow

### 1. Plan The Choice Graph

Agree the shape with the user before drafting; see
`references/choice-graph.md` for the structures, choice design, and
numbering. Then:

1. Draw the graph: every passage, every choice, every rejoin, every ending.
   Count passages and endings against `target-words` and the `form`.
2. Number chapters so each choice leads to a higher number, except a loop
   back. The promise, question, and clue ledgers, the clock and route
   checks, `story pacing`, and the `story diagram` and `story series`
   lifelines still read chapter numbers, so this keeps them close to the
   paths.
3. Scaffold each passage as an outline chapter with its POV and cast, then
   add its `choices` by hand (`story add` does not write them):

   ```shell
   story add chapter 'The Landing' --number 1 --status outline --pov ada-fenn --character ada-fenn --hook decision --path .
   ```

4. Check the skeleton before writing prose. `story links .` warns
   `unreachable-chapter` for every chapter no path from the start reaches,
   and errors on a choice to a missing chapter, except a `chapter-NN` with
   no file yet, which it allows as scheduled. So a typo such as
   `chapter-09` for `chapter-08` passes: compare every `to` with the
   planned passage list by hand, and once every passage has a file, run
   `story build . --format twee`, which refuses any choice to a missing
   chapter.
5. Record the state choices set that the CLI does not track (flags,
   trust, items the reader can carry down one branch) in
   `notes/branch-map.md`, a working file the CLI ignores: a table of each
   flag, the chapter that sets it, and the chapters that read it.

### 2. Draft A Passage

Draft with the `chapter-writing` workflow (outline, approval, prose,
post-write updates), with these differences:

- Run `story context chapter-NN --path .` for every passage. In a branching
  book it holds only what was drafted and learned on a path to that
  chapter, so a sibling branch never leaks in.
- **On a branch:** the passage may use everything on the paths that lead
  to it, and nothing from its sibling.
- **At a rejoin:** the context lists the scenes of every branch that leads
  there. Read each incoming chapter and write only what is true on every
  path: who is where, who is hurt, what the reader has seen. Facts are
  marked known when any incoming path teaches them, so check each fact the
  rejoin uses against every branch. A detail that differs by path stays out
  of the rejoin prose, or is carried by a flag in the built Twine or ink
  file (see Build).
- **At a branch point:** end on the decision (`hook: decision`) and make
  each choice meaningful, informed, and acknowledged in the passage it
  leads to.
- **At an ending:** no `choices`, `hook: resolution`, and an ending that
  pays off the path that reached it. Name it as an ending in the prose if
  the book's style does (`THE END.`).

After saving the passage, record continuity as `chapter-writing` does,
following `references/path-continuity.md` for the branching rules:
deaths and revivals, one `knowledge-state` entry per branch for a fact
learned on two branches, and the `continuity/state.md` snapshot.

### 3. Revise A Branching Book

Use `revision-continuity` for the passes, plus these checks:

- **Reachability:** fix every `unreachable-chapter` by adding a choice that
  leads there, from a passage the user agrees (see Hard Rules). Removing
  the chapter deletes its file and its drafted prose, so offer it only as
  an option, and put the whole removal to the user for one approval:
  1. Take a snapshot (see Draft Snapshots in the `revision-continuity`
     skill).
  2. `remove chapter` refuses while scene files point at the chapter, so
     dry-run each of its scenes: `story remove scene <scene-id> --path .
     --dry-run`.
  3. Dry-run the chapter: `story remove chapter <id> --path . --dry-run`.
     While the chapter still has scenes, this prints only that refusal.
     It also refuses while a `died-in`, `since`, or `learned-in` field,
     or a progression's `from`, names the chapter, so search the project
     for the chapter id and list those references too: each needs another
     chapter before the removal can run.
  4. Show the user every file the dry runs would update and delete, and
     every reference that blocks the removal. Only with their explicit
     approval, repoint the blocking references, remove the scenes, then
     remove the chapter. It drops the choices that led to the chapter and
     warns which chapters became endings.
  5. If the chapter removal is still refused after the scenes are gone,
     stop and ask the user: go on with the next fix, or restore the
     snapshot (`story snapshot --restore <name> --path . --dry-run`
     first, as the `revision-continuity` skill describes).
- **Endings:** list the chapters with no `choices`. Each should be a
  deliberate ending. A chapter that lost its last choice in a revision is
  an accidental ending: give it a choice.
- **Loops:** the CLI does not check that a loop has a way out. Trace every
  loop and confirm a choice leaves it.
- **Path continuity:** run `story continuity .` and read the branching
  findings in `references/path-continuity.md`. Then do the hand checks
  there for what the checker reads by chapter number. Branching books in
  [`../story-maintenance/references/continuity-checks.md`](../story-maintenance/references/continuity-checks.md#branching-books)
  says which `continuity`, `knowledge`, `context`, `timeline`, and `grid`
  results follow the paths and which go by chapter number.
- **Renumbering:** `story move chapter`, `story split`, and `story merge`
  rewrite every `to` that named an old id. Split and merge work here only
  on chapters with no `choices`, and merge only when no choice leads to
  the second chapter; restructure anything else by hand. A split gives its
  first half a `Continue` choice that leads to the rest, so offer the user
  other words for it. None of them edits prose, so reread the passages for
  chapter numbers in the text.
- **Rejoin prose:** after changing a branch, reread every rejoin it leads
  to and confirm the prose still holds on that path.

### 4. Build

```shell
story build . --format twee
story build . --format ink
```

Both write to `dist/` and refuse to build while a choice is malformed or
leads to a missing chapter. Without `ifid:` in `story.md`, they derive the
IFID from the story id and warn with the line to add; add it before
sharing the story, so a retitle keeps the same IFID.

The ink build escapes ink syntax in the prose, so flags and conditional
text (`VAR`, `~`, `{ }`) never go in chapters. Once the graph is settled,
build a working copy with `--out adaptations/interactive/{story-id}.ink`
and write that logic into it by hand. `--out` never replaces an existing
file, so a rebuild after changing `choices` means deleting the old copy and
carrying the hand-written logic into the new one: ask the author before
deleting a file that has hand-written logic in it. Ink and Twine syntax for
that layer is in the `adaptation` skill's
`references/interactive-fiction.md`.

## Maintenance

After adding, removing, renumbering, or rewriting chapters or their
`choices`, run:

```shell
story reindex .
story wordcount . --write
story check .
```

Repair every error. Treat `unreachable-chapter` and `state-differs-by-path`
as findings to resolve or record. `story next .` suggests drafting the next
chapter number, as for a linear book: plan from the graph instead.

If `story` is not installed, use the bundled fallback
`node ../story-maintenance/scripts/story.js` with the same arguments. Use
`node <checkout>/bin/story.js` instead only when the user names a Story
Skills repository checkout or you are working in one. Write the script as an
absolute path (resolve the fallback relative to this skill folder) and run
it from the folder you would run `story` from, so `.` and other relative
paths keep their meaning. Use Node, not Bun or a package script: Bun would
load that folder's `bunfig.toml` (which can run code) and `.env`, and a
package script runs from the checkout's root.

## Hard Rules

- Never invent a branch, ending, or choice the user has not agreed; offer
  options instead.
- Never remove a chapter or scene without the user's explicit approval,
  given after a snapshot and a `--dry-run` that lists what it deletes.
- Never write rejoin prose that is true on only one incoming path.
- Never silence `state-differs-by-path` with an `object-state` entry the
  rejoin chapter's prose does not make true.
- Never put ink logic in chapter prose; keep it in the built copy under
  `adaptations/interactive/`. Write Twine macros in chapters only once the
  author has picked a story format (Harlowe, SugarCube, Chapbook).

## Reference Files

- **`references/choice-graph.md`** - Branching structures, designing
  choices, numbering, rejoins, endings, and scope
- **`references/path-continuity.md`** - What `story continuity` follows by
  path and what it still reads by number, the branching findings and their
  fixes, and the hand checklist

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
