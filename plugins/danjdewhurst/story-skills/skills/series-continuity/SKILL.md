---
name: series-continuity
description: This skill should be used when the user asks to "write a sequel", "write a prequel", "start book two", "continue the series", "companion novel", "spin-off", "link books in a series", "carry characters into the next book", "series continuity", "series bible", "pitch my series", "series pitch", "multi-book pitch", or needs to plan, pitch, or keep canon consistent across multiple Story Skills projects. NOT for a standalone book (use story-init), continuity within one book (use revision-continuity), or a query, pitch, or synopsis for a single book (use submission).
---

# Series Continuity

## Overview

Plan and maintain sequels, prequels, and companion books as linked Story Skills projects. Each book stays a standalone project with its own `story.md`, characters, world, chapters, and continuity files. Books point at each other through `story.md` frontmatter, and `story series` checks the canon they share.

- `series` - kebab-case series id shared by every book, such as `the-ember-cycle`
- `series-title` - optional retail series name, such as `The Ember Cycle`, that the metadata sheet prints in place of the id
- `book-number` - publication order (1, 2, 3...); `0` for a prequel published later, a decimal such as `1.5` for a between-books novella
- `follows` - paths to books set **earlier** in the story's chronology
- `precedes` - paths to books set **later** in the story's chronology

Chronology and publication order are separate. A prequel written after the first book has `book-number: 2` and lists `../book-one` under `precedes`.

This skill owns the book-level layer: linked books and the canon they share. The within-serial installment layer — how serial or episodic installments are structured — is covered by the `genre-craft` skill's serial/episodic structure reference.

Links are relative paths from the book root, and every link needs a matching backlink: if book two lists `../book-one` under `follows`, book one must list `../book-two` under `precedes`. Keep sibling books in the same parent folder so the paths stay short and portable.

## When to Use

- Starting a sequel, prequel, interquel, or companion book to an existing project
- Carrying characters, locations, systems, factions, artifacts, or glossary terms into another book
- Revising a book that other books in the series depend on
- Keeping a series bible, or planning and pitching a series of several books (see `references/series-bible.md`)
- NOT for a single standalone book (use `story-init`), for within-book continuity (use `revision-continuity`), or for the query letter, pitch, or synopsis of a single book (use `submission`). A series pitch stays here: the series overview and the series line in book one's query (see `references/series-bible.md`)

## Starting a Linked Book

1. Read the existing book first: `story.md`, `characters/_index.md`, `worldbuilding/_index.md`, `plot/timeline.md`, `continuity/state.md`, open files in `continuity/questions/` and `continuity/promises/`, and the final chapters.
2. Ask the user for:
   - Title and synopsis
   - Relationship: sequel (set after), prequel (set before), or companion (set alongside, with no chronology link)
   - How much time passes between the books
   - Which characters and places return
3. Create the project with the CLI, run from the folder that contains the existing book:

```shell
# Sequel: set after book one
story init '{Title}' --follows '{existing-book-dir}' --synopsis '{synopsis}'

# Prequel: set before book one
story init '{Title}' --precedes '{existing-book-dir}' --synopsis '{synopsis}'
```

The title and synopsis are the user's own words, and a folder name can hold spaces, so wrap each value in single quotes. Never paste a value into double quotes, where `$(...)`, backticks, and `"` still take effect. A single quote inside a value depends on the shell: write it as `'\''` in a POSIX shell (bash, zsh, sh, Git Bash) and as `''` in PowerShell. Never run the command in cmd.exe, which has no single quotes and runs `&` inside a value; use PowerShell or a POSIX shell.

Run `init` from the folder that contains the existing book, never from inside it: `init` refuses a new book inside another project, and a linked book outside the new book's parent folder. It also refuses a `--series` that differs from the linked book's, and a `--book-number` already used in the series. `init` checks that the linked path is a story project, writes the relative link, adds the backlink (and the new book's `series`, when the existing book has none) to the existing book's `story.md`, and inherits `series`, `genre`, `sub-genre`, `pov`, and `tense`, plus `series-title`, `author` or `authors`, and `language` when the linked book sets them. When any book in the linked series has a `book-number`, it sets `book-number` to one more than the highest whole number used anywhere in the series, so publication numbers never collide. A normal `story init` book has none, so a series with no numbered books leaves the new book unnumbered. Pass `--book-number` (or write the field on both `story.md` files) in that case. Pass `--series`, `--genre`, `--pov`, or `--tense` to override the inherited values.

If the existing book has no `series` yet, pass `--series {series-id}`: `init` also writes that `series` into the existing book's `story.md`. Add matching `book-number` values to both `story.md` files yourself.

If the CLI is not available, add the fields to both `story.md` files by hand.

4. Add a `## Series Notes` section to the new `story.md` body. Record where the book sits in the chronology, the time gap, and the canon facts it must not contradict. `references/series-bible.md` covers what to put in it.

## Carrying Canon Across Books

Only carry entities the new book actually uses. For each one, copy the file from the other book and then adjust it:

- **Keep the filename id identical.** `story series` matches entities across books by id. A renamed file is a new entity to the checker. `story rename` warns when the id is also defined in a linked book; rename it there too, or keep the old id.
- **Keep `name` identical.** Put new titles or epithets in `aliases`, such as `General Maren` in a prequel for `Lord Maren`. A different `name` produces a warning, and so does a different `pronunciation`.
- **Set state for this book's starting point, not the source book's ending.**
  - Sequel: start from the earlier book's final `status`, relationships, ownership, and knowledge.
  - Prequel: start from the earlier situation, and write the later book's facts as fixed endpoints in a `## Series Canon` section.
- **Remove book-local references.** `died-in`, the `from` of each `progressions` entry, and every other chapter id point at chapters in the source book. Set the frontmatter to the state the character starts this book in, and drop the source book's `progressions`. For a character who died before this book begins, by `died-in` or by a status progression, keep `status: deceased`, remove `died-in`, and list them only in `mentions`: `story continuity` warns when one appears in a chapter or scene cast. If they come back in this book, add a status progression to `alive` from that chapter; `story series` then allows them on the page from there.
- **Prune or carry every link.** Relationships, `locations`, `notable-characters`, faction `members`, and artifact `owner`/`location` must point at entities that exist in this book, with backlinks. Either carry the linked entity too, or remove the reference.
- **Do not copy** chapters, scenes, arcs, questions, promises, or `continuity/state.md`. Rebuild them for the new book:
  - Unresolved questions or promises the new book continues become new files in its `continuity/` folders.
  - Events from the other book become `Backstory Events` rows in `plot/timeline.md` (sequel) or `Series Canon` notes (prequel).
  - `continuity/state.md` starts at `current-chapter: 0` with the carried character and object state. Carried knowledge goes in `knowledge-state` without `learned-in`, because the character already knew it when the book began.
  - An artifact destroyed or lost in an earlier book keeps its `object-state` entry with `status: destroyed` (or `lost`) and no `since`: that marks it gone before this story, so `story continuity` errors on any scene whose `state-changes` use it while still allowing `mentions`.

## Fact Ids

Give series-relevant knowledge a stable `fact` id in `continuity/state.md`, and use the same id in every book:

```yaml
knowledge-state:
  - character: kael-voss
    knows: The gallery tunnel reaches the Whisper Gate
    fact: whisper-gate-route
    learned-in: chapter-04
```

- Fact ids are kebab-case, and each character lists a given fact only once per book. `story continuity` checks both rules.
- Add `learned-in` only in the book where the character discovers the fact on the page. In later books, carry the entry without `learned-in`. Do not put that rule in an inline comment: a command that rewrites the entry drops the comment.
- Reuse the exact id in every book. The checker matches the character id plus the fact id, never the `knows` text.
- Give ids to the reveals, secrets, and discoveries a later or earlier book depends on. Everyday knowledge does not need one.

After carrying entities, run in the new book:

```shell
story reindex .
story wordcount . --write
story check .
story series .
```

## What `story series` Checks

`story series [path]` follows `follows` and `precedes` to every linked sibling book, orders the books by chronology, lists the canon they share, and reports deaths, casts, learned facts, and destroyed artifacts that contradict an earlier book, and names or pronunciations that drift from it. Errors exit 1. Fix each one in the book that breaks canon (in a prequel, the later book is canon), move a dead character's flashbacks and memories to `mentions`, and ask the user before changing an earlier book. Treat warnings as prompts to check the named files. `story series --help` describes the command and, when `story-maintenance` is installed, the series section of [`../story-maintenance/references/continuity-checks.md`](../story-maintenance/references/continuity-checks.md#series) lists every error and warning and the order rules.

`story links .` also checks the book's own series links: each path exists, has a matching backlink, and uses the same `series` id.

The checker cannot judge knowledge without fact ids, or ages, dates, travel time, or tone. Check those by reading both books' timelines and `Series Canon` notes.

## Writing Against Canon

- **Sequels:** before drafting, reread the earlier book's final chapters, `continuity/state.md`, and every unresolved question or promise. Decide with the user which threads the new book picks up.
- **Threads left for the next book:** a promise, question, or clue that pays off in a later book stays open in this one. `story continuity` warns about a planted promise or clue while drafting (the Chekhov gap: `promise-unpaid` or `clue-unpaid`) and about an open question once twelve drafted chapters follow its `introduced` chapter (`question-unanswered`). It errors once `story.md` is `complete` (`is still planted`, `is still open`). Record each deliberate one in this book's `continuity/exemptions.md` (the finding's `code` and `file`, such as `code: promise-unpaid` and `file: continuity/promises/the-sealed-letter.md`, or `code: question-unanswered` and `file: continuity/questions/who-kept-the-key.md`, plus a `reason` naming the book that pays it off; once `story.md` is `complete` the code is `complete-with-open-promise` or `complete-with-open-question` and the file `story.md`, so add a `pattern` naming the promise or question file) rather than marking it `paid-off`, `resolved`, or `dropped`, and add the matching file to the later book's `continuity/` folders.
- **Prequels:** the later book is canon. Every fixed endpoint must still be reachable by the end of the prequel. Do not mark a character `deceased` who is alive in a later book. Do not give a character knowledge that the later book shows them learning for the first time. Before drafting, list the later book's `fact` ids that have `learned-in`, and keep those facts out of the prequel's knowledge.
- **Revising an earlier book** after later books exist: run `story series .` before and after the revision. Update the later books' `Series Notes` and carried entity files when canon changes.

## Maintenance

After any change to series links or carried entities, run the checks in each affected book:

```shell
story reindex .
story wordcount . --write
story check .
story series .
```

If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root.

## Conventions

- One project folder per book, with books side by side in a shared parent folder
- `series` ids are kebab-case and identical in every book
- Entity ids and `name` values stay stable across books; variants go in `aliases`
- Chronology goes in `follows`/`precedes`, publication order in `book-number`
- Every link needs a matching backlink in the other book

## Reference Files

- **`references/series-bible.md`** - Where each part of a series bible lives across the linked books, writing `Series Notes`, keeping canon current, planning a multi-book series, and pitching one (query line and `submission/series-pitch.md` template)

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
