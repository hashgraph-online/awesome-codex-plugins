---
name: editorial-review
description: This skill should be used when the user asks for a "sensitivity reader", "authenticity reader", "cultural review", "is this portrayal okay", "real people in my novel", "defamation", "can I use song lyrics", "epigraph permission", "permissions", "quote permission", "fair use", "AI disclosure", "do I need to disclose AI", "send to my editor", "editorial round", "Word file for my editor", "editor review copy", "co-author", "collaborate on a book", "shared world", "back up my book", "does this echo my source", "similarity check", "check overlap with my earlier books", or wants to run human editorial, ethics, permissions, or collaboration workflows around a story project. NOT for contracts or selling rights (use publishing), or reader feedback rounds and review copies for readers, including the GitHub review-copy setup (use feedback-triage).
---

# Editorial Review

## Overview

Run the workflows that involve people outside the agent: briefing and
paying sensitivity and authenticity readers, a real-people and
defamation-risk pass, permissions for quoted material, an AI-use
disclosure statement, editorial rounds with human editors, and
collaboration between co-authors. The skill prepares materials, tracks
state in frontmatter, and flags risks. It does not give legal advice, it
does not contact anyone, and it never records a permission, review, or
disclosure the user has not confirmed.

## Prerequisites

A story project with `story.md` in the root and drafted chapters. Git is
needed for snapshot tags, `story compare --ref`, and the collaboration
workflow; offer `git init` if the project has none.

## When to Use

- A book portrays a culture, identity, disability, faith, trade, or
  experience the author does not share
- Fiction features or resembles real, identifiable people or organisations
- The manuscript quotes lyrics, poems, epigraphs, or other writers' prose
- A passage may echo a source, an earlier book, or another writer too closely
- The user needs an AI-use statement for a retailer, agent, or publisher
- Sending the manuscript to a human editor, or taking their edits back
- Two or more people write or maintain the same book or shared world
- NOT for synthesising reader notes into decisions (use `feedback-triage`; this skill hands notes to it)
- NOT for fact-checking real-world details (use `research`; this skill adds the review layer on top)
- NOT for the agent's own prose edit (use `line-editing`) or structural revision (use `revision-continuity`)
- NOT for query letters, synopses, or retailer copy (use `submission`)

## Workflow

### 1. Sensitivity and authenticity reads

1. Find what needs a read: characters, settings, and research notes that
   touch lived experience the author lacks. Mark the research notes that
   ground them by adding `cultural` to the note's `risk` list (add
   `medical`, `legal`, or others as they apply), or open one:

   ```shell
   story add research 'Deaf community in 1980s Glasgow' --accuracy must-be-accurate --method expert-review --risk cultural --used-in chapter-04
   ```

2. Prepare the brief with `references/sensitivity-reader-brief.md`: which
   chapters, which characters, specific questions, the author's research
   so far, deadline, and fee. Sensitivity reading is paid professional
   work; help the user budget and find readers, never suggest asking
   community members to work for free.
3. Build what the reader receives: `story build . --format docx` for
   readers who comment in Word, or `story build . --format html` for
   paragraph-anchored notes.
   A `reader-panel` round's sensitivity persona can point at passages to
   put in the brief, but it is not a sensitivity read: never record it in
   `reviewed-by` or treat it as clearing a portrayal.
4. Record the returned notes as a feedback round (`feedback/round-{N}/`)
   and synthesise them through the `feedback-triage` skill. When the
   reader's notes are incorporated, add them to the research note's
   `reviewed-by` (name or role, with their consent to be named).
5. `story validate .` warns when a note with any `risk` is used in a
   `final` or `complete` chapter and has no `reviewed-by`.

### 2. Real-people and defamation pass

For fiction that uses real people, real organisations, or recognisable
portraits, follow `references/real-people-and-permissions.md`: list every
real or recognisable person, classify each portrayal, and flag the risky
ones in a research note by adding `defamation` (or `legal`) to its
`risk` list. Say
plainly that this is a flagging exercise, not legal advice, and recommend
a publishing lawyer's review before publication whenever a living person
or a real organisation is shown doing something discreditable.

### 3. Permissions for quoted material

1. Find every quotation of someone else's work: epigraphs, lyrics,
   poems, extracts, and in-text quotes. Each epigraph or quoted page
   usually lives in `matter/`.
2. Record state in the matter file's frontmatter: `permission`
   (`not-needed`, `pending`, `granted`, `public-domain`), `rights-holder`,
   and `credit` (the exact credit line the rights-holder requires).
3. Apply the cautions in `references/real-people-and-permissions.md`:
   song lyrics almost always need permission, fair use is a narrow and
   uncertain defence, and public-domain status depends on country and
   date. Never set `granted` or `public-domain` without the user's
   confirmation and, for `granted`, the rights-holder's name.
4. `story validate .` warns when a matter page is `pending` and the story
   is `complete`, and when `granted` has no `rights-holder`. Whatever the
   status, `story export` and the builds leave a `pending` page out (the
   review copy too) and warn `permission-pending-left-out`, unless
   `--include-pending` is given.

### 4. Overlap with other text

When the user worries that a passage echoes a source, an earlier book, or
another writer too closely, compare the chapters with that text:

```shell
story similarity . --against ../sources
story similarity . --against ../book-one --min-words 12
```

`--against` takes a file, a folder, or a git ref. Each run of shared
words is a warning with both locations and the words.

Report the result honestly:

- Say what was compared and what was not. The check only sees the text
  passed to `--against`. It says nothing about other books, the web, or
  sources nobody gave it, so never tell the user a manuscript is
  "original", "clean", or "plagiarism-free" on its strength.
- Shared text is not plagiarism. Stock phrases, a quotation the author
  meant, and the author's own recurring lines all share words. List each
  passage with its locations and let the user decide what it is. Never
  call a passage copied.
- A passage quoted on purpose from another writer belongs in the
  permissions pass (section 3), not in a rewrite.
- A passage that should not be there is rewritten by the author, or with
  the `line-editing` skill at the author's direction. Never paraphrase it
  quietly to make the match disappear.
- Where a matching passage came from AI-assisted drafting, raise it when
  drafting or revisiting `ai-disclosure` (section 5): the statement
  describes how AI was used, and the similarity result neither proves nor
  disproves AI use.

### 5. AI-use disclosure

1. Ask the user how AI tools were used on this book: brainstorming,
   outlining, drafting prose, editing, research, cover or art, or
   translation, and roughly how much of the published text was generated
   rather than written or rewritten by the author.
2. Draft a short plain statement for `ai-disclosure` in `story.md`, for
   example: `Outlining and line-level editing suggestions used an AI
   assistant; all prose was written and revised by the author.` Use only
   what the user confirms; never minimise or inflate it.
3. Tell the user that disclosure expectations differ and change: some
   retailers ask at publication whether content is AI-generated or
   AI-assisted, many agents and publishers ask in submission guidelines
   or contracts, and some magazines do not accept AI-generated work. Ask
   the user to check the current terms of each retailer, agent, publisher,
   or market they submit to; do not quote policy text from memory.
4. `story build . --format metadata` includes the statement on the
   retailer metadata sheet.

### 6. Editorial rounds with a human editor

Follow `references/editor-rounds.md`:

1. Snapshot and tag the draft sent (`sent-to-editor-1`). From the
   book's folder (the one with `story.md`), check that `.gitignore`
   lists `dist/`, show the user `git status --untracked-files=all -- .`,
   and ask about any private file it lists (a `.env`, keys, scans). With
   the user's approval, commit the book's folder only and tag it:
   `git add -A -- . && git commit -m "…" -- . && git tag sent-to-editor-1`.
   When the status lists nothing, run only the tag; if the user declines
   the commit, or it fails, never tag over the uncommitted tree. Then
   build the file the editor wants: `story build . --format docx` (Word
   with Track Changes) or `story build . --format shunn` for manuscript
   format.
2. When edits come back, the author accepts or rejects them in Word; the
   agent transfers the accepted text into the chapter markdown, chapter
   by chapter, never by a bulk script. Queries that change events go to
   `revision-continuity`; editorial letters go through `feedback-triage`.
3. Show how deep the round went: `story compare . --ref sent-to-editor-1`.

### 7. Review copies for non-technical readers

For editors, sensitivity readers, or agents who never open a terminal,
`story build . --format html` produces one file with a table of contents
and a clickable paragraph label on every paragraph (`ch03-p12`), so
comments can cite exact places in email, a doc, or an issue. To publish
the copy on GitHub Pages with an issue form for notes, follow the GitHub
review copy setup in step 1 of the `feedback-triage` workflow, which has
the details. Even without that skill, warn first that a public Pages site
makes the manuscript public unless the repository and Pages are private,
confirm the visibility the user wants, and ask before creating any file
in `.github/`. Collect the notes that come back into a feedback round
and triage them with `feedback-triage`. Resolve labels from an older build with
`story compare . --ref <round-tag> --anchor '<label>'` before acting on
them; see `references/editor-rounds.md`.

### 8. Collaboration and backups

Follow `references/collaboration.md` for co-authored books and shared
worlds: list every author under `authors` in `story.md`, one branch per
author or per chapter, pull requests to `main`, a `CODEOWNERS` file for
shared-world canon, and a remote pushed after every session as the
backup. Real-time collaborative editing (two people typing in one file at
once) is out of scope for the markdown model; recommend taking turns per
file through branches instead.

## Conventions

- Never record a review, permission, credit, or disclosure the user has
  not confirmed. Unknown values stay `pending` or unset.
- Flag risk; do not give legal advice. Recommend a qualified lawyer for
  defamation, privacy, or permission questions on a book going to
  publication.
- Reviewers are named in `reviewed-by` only with their consent;
  otherwise record their role (`sensitivity reader, Deaf culture`).
- Sensitivity notes are input to the author, not verdicts. The author
  decides, and `feedback-triage` records declined notes with a reason.
- Never send, email, upload, push, or publish anything without the
  user's instruction. The user contacts readers, editors, and
  rights-holders.
- Never commit, tag, push, or change branches without the user's approval.

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
available, keep the frontmatter fields current by hand, and leave the
`research/_index.md` and `matter/_index.md` tables to the next
`story reindex .`: never edit their rows.

After adding or editing research notes, matter pages, `story.md`
metadata, or chapters:

```shell
story reindex .
story wordcount . --write
story check .
```

## Reference Files

- **`references/sensitivity-reader-brief.md`** - When to hire a sensitivity or authenticity reader, finding and paying them, a brief template, and incorporating notes
- **`references/real-people-and-permissions.md`** - Real-people and defamation-risk pass, permissions for epigraphs, lyrics, and quotations, and the matter-file permission fields
- **`references/editor-rounds.md`** - Sending a manuscript to a human editor, snapshot tags, taking DOCX edits back into markdown, and HTML review copies with paragraph anchors
- **`references/collaboration.md`** - Multi-author projects, git branching per author, CODEOWNERS for shared worlds, and backups

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
