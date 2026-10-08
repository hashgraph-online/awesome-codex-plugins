---
name: premise-workshop
description: This skill should be used when the user asks to "brainstorm a story idea", "I have an idea for a story", "what if", "develop a premise", "is this idea strong enough", "workshop my logline", "premise", "story concept", "what should I write", "short story or novel", "novella or novel", "name my book", "title ideas", or has a spark (an image, a character, a setting, a question) and wants to turn it into a tested premise before starting a story project. NOT for the controlling idea or theme of an existing story (use theme-craft).
---

# Premise Workshop

## Overview

Turn a spark into a premise that can carry a book, before `story init`
builds the project. The workshop generates what-ifs from the spark, tests
them as loglines, drafts the controlling idea and its counter-argument
(`premise` and `counter-premise` in `story.md`), names the stakes, chooses
a form (the `form` field), brainstorms titles, sanity-checks the idea
against comparable books, and hands a filled-in brief to the `story-init`
skill. The author owns the idea: offer options and tests, never decide for
them.

## Prerequisites

None. The workshop usually runs before a project exists. If the user wants
the work saved before `story init`, keep it in one `premise-notes.md` file
in the current directory (outside the future project folder) and move the
kept material into `story.md` after init.

## When to Use

- The user has a spark but no premise, or several ideas and cannot choose
- The user has a premise and wants to know whether it holds up
- Choosing between short story, novella, novel, serial, or a children's form
- Brainstorming a title, or checking a working title against the cast
- NOT for creating the project folder (use `story-init`; this skill hands off to it)
- NOT for refining the controlling idea of a drafted book, arc types, or the lie/truth machinery (use `theme-craft`)
- NOT for outlining once the premise is settled (use `plot-structure`, or `discovery-drafting` for pantsers)
- NOT for comp titles, pitch, or blurb for submission (use `submission`)

## Workflow

### 1. Capture the spark

Ask what the user has, in their words, and do not improve it yet. Ask
which language the book will be written in if it is not clear, and
workshop in that language: what-ifs, loglines, and titles are drafted in
it, and comps come from the market that reads it. Sort it:
an **image** (a drowned bell tower), a **what-if** (what if grief could be
sold), a **character** (a lighthouse keeper who has never left the rock),
a **setting** (a city that moves every winter), or a **feeling** they want
a reader to have. Ask what drew them to it. The answer is often the book's
real subject and should survive every later change.

### 2. Generate what-ifs

Following `references/what-if-generation.md`, produce 8-12 short what-ifs
from the spark across different angles (invert it, raise the cost, move it
in time or place, give it to the wrong person). Present them as a numbered
list and ask the user to pick one to three, or to combine. Do not rank them
for the user unless asked; do say which ones already imply conflict.

### 3. Workshop the logline

For each chosen what-if, draft a logline with the recipe in
`../story-init/references/title-logline.md` (protagonist + want + obstacle
+ stakes). Then run every logline stress test in
`references/premise-tests.md`. Report each test as pass, weak, or fail
with one sentence of why, and offer one revision per weak or failed test.

### 4. Draft premise and counter-premise

`story.md`'s `premise` field is the controlling idea (value + cause), not
the logline. Draft it and the `counter-premise` as working hypotheses
using `../theme-craft/references/controlling-idea.md`. If the user wants
to discover theme in the draft, record `premise: tbd-discovery` and move
on. Keep the logline for the Synopsis section.

### 5. Name the stakes

Write the stakes on three levels (see `references/premise-tests.md`):
external (what is lost in the world), relational (who is lost or
betrayed), and internal (what the protagonist becomes if they fail). At
least two levels must be concrete and personal.

### 6. Choose the form

Use `references/form-choice.md` to match the idea's scope to a form:
`novel`, `novella`, `novelette`, `short-story`, `flash`, `serial`,
`picture-book`, or `chapter-book`. Count the idea's moving parts (POV
characters, threads, locations, time span) and recommend the form they
fit, with the trade-offs. The user decides.

### 7. Brainstorm titles

Follow `references/title-and-comps.md`: generate titles across the
families listed there, cut to a shortlist of five, and test each against
the logline and the genre shelf. The title craft principles live in
`../story-init/references/title-logline.md`; do not repeat them to the
user, apply them.

Once a project exists, check title words and new names against the story's
entities before adopting them:

```shell
story names 'Bell Tower' Bell 'Maren' --path .
```

An exact clash exits 1 and must be resolved; look-alike warnings and a
shared initial with a major character are the user's call. Multi-word
names are only checked for exact clashes, so pass a multi-word title's
distinctive word separately, as `Bell` is above. The "Check names
against the project" section of `references/title-and-comps.md` says what
each finding means and how to resolve a clash.

### 8. Sanity-check against comparable books

Ask the user for two or three recent books the idea sits beside. Use
`references/title-and-comps.md` to check whether the premise is
distinct from them and whether it fits the shelf they imply. Never invent
titles, authors, or sales claims; if web search is available, verify that
each named book exists and note what you checked. If not, mark the list
unverified.

### 9. Hand off to story-init

Present a one-screen brief: working title, logline, premise,
counter-premise, stakes, form, genre and sub-genre, POV and tense if
known, themes, the comps, and the book's language as a BCP 47 tag (`en`,
`fr`, `es-MX`, `ja`). On approval, follow the `story-init` skill
with the brief:

```shell
story init 'The Keeper of Skerry Light' --form novella --genre fantasy --sub-genre coastal --synopsis 'A lighthouse keeper who has never left the rock must choose between the light and her drowned brother.' --theme isolation
```

Workshop text is the user's own words, so wrap every value in single
quotes before running the command. Never paste a value into double
quotes, where `$(...)`, backticks, and `"` still take effect. A single
quote inside a value depends on the shell: write it as `'\''` in a POSIX
shell (bash, zsh, sh, Git Bash) and as `''` in PowerShell. Never run the
command in cmd.exe, which has no single quotes and runs `&` inside a
value; use PowerShell or a POSIX shell.

`--form` sets `form` in `story.md` and a default `target-words` for the
form when none is given (`serial` sets none; set per-episode chapter
`target-words` instead). The form defaults and `references/form-choice.md`
lengths are English word counts; for a book in another language, discuss
the target with the user. A Chinese (`zh`) or Japanese (`ja`) book is
counted in characters: talk about length in characters (10万字, or
sheets of 400字 for Japanese), and once `language` is in `story.md`,
replace `target-words` with `target-characters` (the story-init skill
lists the per-form defaults). Then hand-edit `premise`, `counter-premise`,
and `language` (the tag from the brief) into `story.md`, and move the stakes, rejected what-ifs worth keeping,
title shortlist, and comps into its `## Notes` section. Keep
`premise-notes.md` if one was made: offer to move it into the new
project as `notes/premise-notes.md`, and delete it only when the user
asks after seeing what was carried over.

## Conventions

- Present options, not verdicts. The user chooses the what-if, form, and
  title; record why when they reject a recommendation.
- Keep the spark's original wording in the notes. Premises drift during
  workshop; the spark is the check that the drift was chosen.
- `premise` in `story.md` is always the controlling idea (value + cause).
  The logline goes in the Synopsis section.
- Titles and names are provisional until `story names` passes. Rename a
  title freely before chapter one, then run `story reindex .`: the story
  id in every registry, `plot/timeline.md`, and `continuity/state.md`
  follows the `story.md` title, so `story validate` fails until they are
  rewritten. After chapter one, rename a character with
  `story rename character <id> '<New Name>' --prose`, so the chapter text
  follows as well as the references: run it with `--dry-run` first, show
  the user the replacements, and run it for real only once they approve.
  Without `--prose` the prose keeps the old name.
- Never present a comparable title, author, prize, or market fact as
  verified without a source.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the
bundled fallback `node ../story-maintenance/scripts/story.js` with the same
arguments. Use `node <checkout>/bin/story.js` instead only when the user
names a Story Skills repository checkout or you are working in one. Write
the script as an absolute path (resolve the fallback relative to this skill
folder) and run it from the folder you would run `story` from, so `.` and
other relative paths keep their meaning. Use Node, not Bun or a package
script: Bun would load that folder's `bunfig.toml` (which can run code) and
`.env`, and a package script runs from the checkout's root. If no CLI is
available, create the project by hand as the `story-init` skill describes
and check names against the registries by reading them.

After `story init` and the hand edits to `story.md`:

```shell
story reindex .
story wordcount . --write
story check .
story report .
```

`story check` warns when `target-words` (`target-characters` for
Chinese or Japanese) sits outside the chosen form's usual range; either
adjust the target or confirm the choice with the user.
`story reindex .` is needed only when the title changed, but it is safe to
run every time.

## Reference Files

- **`references/what-if-generation.md`** - Angles for turning an image, character, setting, or question into conflict-bearing what-ifs, with worked examples
- **`references/premise-tests.md`** - Logline stress tests, the three levels of stakes, and common premise failures with fixes
- **`references/form-choice.md`** - Matching an idea's scope to a form: moving-parts count, what each form does well, and the `form` values
- **`references/title-and-comps.md`** - Title brainstorming families, shortlist tests, `story names` checks, and the comparable-title sanity check

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
