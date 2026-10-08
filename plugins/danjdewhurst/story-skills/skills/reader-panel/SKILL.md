---
name: reader-panel
description: This skill should be used when the user asks for a "simulated beta read", "reader panel", "persona read", "first read before my beta readers", "how would a genre reader react", "would a reader keep going", "pre-beta read", "mock beta readers", or wants structured persona reads of a chapter range before human readers see it. NOT for real reader feedback (use feedback-triage), a paid sensitivity or authenticity read (use editorial-review), or the agent's own line edit (use line-editing).
---

# Reader Panel

## Overview

Run structured persona reads of a chapter range and write each one as a
feedback file in the shape `feedback-triage` already reads, so the
existing triage flow takes over unchanged. The panel is a first read
before human readers see the draft: it finds the problems a reader would
trip on, so the human round spends its attention on what only people can
tell you.

Every panel read is simulated. It is written by the agent, marked
`source: simulated`, and never presented as feedback from a real reader.

## Prerequisites

A story project (`story.md` in the root) with the chapters in range
drafted. The `feedback-triage` skill must be available for the synthesis.

## When to Use

- Before the first beta round, to catch the obvious problems cheaply
- After a revision, to check a fix landed before sending it to people
- When the user has no readers yet and wants a structured first read
- NOT as a substitute for human readers. A simulated round cannot close
  a book as `ready` for submission or publication
- NOT for a sensitivity or authenticity read. The sensitivity persona
  only flags passages for a paid human reader (use `editorial-review`)

## Personas

Each persona has a reference file listing what it reads for, what it
never comments on, and how it rates severity. Load only the personas in
the panel.

| Persona | File id | Reads for | Reference |
|---------|---------|-----------|-----------|
| Target-genre reader | `genre-reader` | Does the book deliver the genre's promises? Pacing sags, missing beats, broken conventions | `references/genre-reader.md` |
| Line editor | `line-editor` | Sentence-level craft: POV slips and head-hopping, filter words, repetition, unclear antecedents, voice drift | `references/line-editor.md` |
| Sensitivity reader | `sensitivity-reader` | Portrayals that need a human sensitivity or authenticity reader. Flags, never clears | `references/sensitivity-reader.md` |
| Continuity-minded reader | `continuity-reader` | Facts, names, objects, timeline, and what each character can know at this point | `references/continuity-reader.md` |
| First-page reader | `first-page-reader` | Would they keep going? The opening page, each chapter's first lines, and the last line before they could put it down | `references/first-page-reader.md` |

## Workflow

### 1. Scope the panel

1. Ask the user for the chapter range (default: every drafted chapter)
   and which personas to run (default: all five). Take genre, form, POV,
   and tense from the `story context` output in step 2 (its Story
   essentials section), not from `story.md`, whose Synopsis may describe
   the ending. The genre reader needs the genre. Take `language` only from
   the Language contract in that same `story context` output: it is no
   spoiler, and every persona reads the book as a reader of that language
   would.
2. Pick the round number: the next `N` that is free under `feedback/`
   and not yet the name of a tag or snapshot `panel-round-{N}`
   (`git tag --list 'panel-round-*'` and `story snapshot --list --path .`
   list them). A panel gets its own round. Never add simulated reads to
   a round of human readers, so the human synthesis stays independent.
3. Save the text the panel will cite under the name `panel-round-{N}`,
   so `feedback-triage` can map its labels to a later draft with
   `story compare` once the chapters change:

   - **Git project:** work from the book's folder, the one that holds
     `story.md` (`cd` there first), because `-- .` below means the
     current folder. Check that `.gitignore` lists `dist/` (add the line
     if it is missing), so earlier review copies stay out of the commit.
     Then run `git status --untracked-files=all -- .` and show the user
     what it lists: the copy is built from the working tree, but a tag
     points at the last commit, so uncommitted changes would make the two
     differ. Look through it for private files (a `.env`, keys or
     credentials, scanned documents): unless the user says to commit one,
     add it to `.gitignore` first. `.gitignore` does not untrack a file
     git already tracks, so also run `git ls-files -- .` and look for the
     same kinds of file: if one is listed, the commit below would include
     its changes, so stop and ask the user before committing. A tag holds only
     tracked files, so run `git ls-files --others --ignored
     --exclude-standard -- .` as well: if it lists a markdown file outside
     `dist/` and `.snapshots/`, or the cover or stylesheet `story.md`
     names, the build reads a file the tag would miss, so take a snapshot
     as below instead. Ask before committing and before tagging. With
     approval, commit the project folder only (skip the commit when the
     tree is already clean) and tag that commit:

     ```shell
     git add -A -- .
     git commit -m "Simulated reader panel round {N}" -- .
     git tag panel-round-{N}
     ```

     If the user declines the commit, never tag the last commit over an
     uncommitted tree: take a snapshot as below, or stop. If `git tag`
     says the tag already exists, an earlier attempt saved this round:
     never move it; ask the user, or pick the next free `N`. Never push,
     and never move or delete a tag, without the user's approval.
   - **Project without git, the user declined the commit, or an ignored
     file the build reads:** take a snapshot with
     `story snapshot panel-round-{N} --path .`.

4. Build the review copy the panel cites from that text, so its labels
   match the ones human readers will use:

   ```shell
   story build . --format html --stamp panel-round-{N}
   ```

   The build holds the whole book, so use it for labels only: a persona
   reads the chapter files in range, never the review copy. Cite each note
   with its paragraph label (`ch03-p12`) and the paragraph's first few
   words, exactly as the feedback template asks of human readers.

### 2. Gather context without spoilers

A persona reads the book as a reader would: only the chapters in range,
in order. For background (who the characters are, what the story has
promised so far), run `story context` on the last chapter in range:

```shell
story context chapter-{NN} --path . --budget 4000
```

It leaves out later chapters and the synopsis. Its `What <name> knows that the reader has not seen (do not reveal)` subsection holds facts from chapters the reader has not reached: delete that whole subsection, heading included, before any persona sees the output. Do not
read `story.md` (the context already gives its `language`), `plot/`, arc files, promise payoffs, or chapters after the
range: a persona
that knows the ending cannot tell whether the setup works. When the
genre reader needs the genre's promises, take them from the chapters and
the genre, not from the outline.

### 3. Run each read independently

1. Run one persona at a time. If you can start subagents, give each
   persona its own subagent with only its reference file, the chapters in
   range, the `story context` output, and the book's language, so no
   persona reads another's notes. The line editor's subagent also gets
   `style-sheet.md` (when the project has one) and the `story prose .`
   findings for the chapters in range. Run `story prose .` first, and keep
   only its per-chapter findings for chapters in range. Otherwise finish and
   save one persona's file before starting the next, and do not revise
   earlier files after reading later ones.
2. Follow the persona's reference file. Read the whole range before
   writing any note.
3. Every problem cites evidence: the paragraph label, the quoted first
   words, and the words that cause the problem. A note with no location
   in the text is not a note; drop it.
4. Report what the persona finds, not a quota. A persona that finds
   nothing writes that in **Overall Impression** and leaves **Problems**
   empty. Never pad a read to look thorough, and never invent a problem
   another persona or a craft checklist would expect.
5. Read in the book's language. Judge prose, dialogue, and punctuation
   by that language's conventions and the style sheet, not English ones:
   guillemets or dialogue dashes are not errors in a French or Spanish
   book. Quote the text exactly as written, and write the notes in the
   language the user works in with you unless they ask otherwise.
6. Mark uncertainty. When a note depends on something the persona cannot
   see (a later payoff, the author's intent), say so in the note instead
   of asserting it.

### 4. Write the files

Write each read to `feedback/round-{N}/{persona}.md` using
`../feedback-triage/references/feedback-template.md`, with these
frontmatter values:

```yaml
---
reader: "{Persona name} (simulated)"
round: {N}
chapters-read: "{range}"
overall-verdict: "{loved it | liked it with reservations | mixed | didn't connect}"
source: simulated
persona: {file id from the table}
---
```

Leave each note's **Canon check** line as `not checked (simulated read)`:
checking against the bible means reading past the range, so
`feedback-triage` does it at synthesis. Severity uses the template's scale
(`blocking`, `major`, `minor`, `nit`), rated by the persona's reference
file; some personas use only part of it (the sensitivity persona never
rates a note `blocking`, and the first-page reader has no `nit`).

### 5. Hand off to feedback-triage

Hand the round to the `feedback-triage` skill for synthesis, and tell it
whether step 1 saved the text as a tag or as a snapshot named
`panel-round-{N}`. It maps a label to the current text with
`story compare . --ref panel-round-{N} --anchor '<label>'`, or with
`--snapshot panel-round-{N}` in place of `--ref` for a snapshot. It reads
`source: simulated` and weighs the round accordingly: agreement between
personas is not independent convergence, and a simulated round's
`ready` verdict means ready for human readers, nothing more. Tell the
user plainly that the notes are simulated, and which personas ran.

## Conventions

- Panel files live under `feedback/round-{N}/`, one per persona, named by
  the persona's file id: `feedback/round-2/line-editor.md`.
- Every panel file carries `source: simulated` and `persona`. A file
  without them is a human reader's file.
- A panel round holds only simulated reads. Human and simulated reads are
  never mixed in one round.
- Never describe a simulated read as a reader's, a beta reader's, or a
  sensitivity reader's feedback, in chat, in commit messages, in the
  synthesis, or in anything the user might send on.
- Do not revise the manuscript during the panel. The revision plan comes
  from the synthesis, as for a human round.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, read the chapters in range directly and cite chapter and paragraph positions by hand.

The CLI does not read `feedback/`, so panel files never cause validation
errors. Save the text as `panel-round-{N}` (a git tag, or
`story snapshot panel-round-{N} --path .`), then run
`story build . --format html --stamp panel-round-{N}` for the labels and
`story context chapter-{NN} --path .` for spoiler-safe background.
When the synthesis adds or resolves `continuity/questions/` entries, run:

```shell
story reindex .
story wordcount . --write
story check .
```

## Reference Files

- **`references/genre-reader.md`** - The target-genre reader: the genre's promises, pacing, and conventions, and how to rate a missed beat
- **`references/line-editor.md`** - The line editor: POV slips, filter words, repetition, antecedents, and voice drift at the sentence level
- **`references/sensitivity-reader.md`** - The sensitivity persona: flags portrayals for a paid human reader, never clears one
- **`references/continuity-reader.md`** - The continuity-minded reader: facts, names, objects, timeline, and character knowledge within the range
- **`references/first-page-reader.md`** - The first-page reader: whether they would keep reading, and where they would stop

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
