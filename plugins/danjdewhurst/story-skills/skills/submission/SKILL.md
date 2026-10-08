---
name: submission
description: This skill should be used when the user asks to "write a query letter", "query", "querying", "pitch", "blurb", "back cover copy", "jacket copy", "comp titles", "comparable titles", "synopsis for agents", "submit to agents", "submission tracker", "self-publishing description", "retailer description", "ready to query", "submission readiness check", "submit a short story", "magazine submission", "short-fiction markets", "simultaneous submission", "reprint rights", "order a short story collection", or wants to prepare and track a finished manuscript's submission to agents, publishers, magazines, anthologies, or retailers. NOT for pitching a series of several books (use series-continuity), or self-publishing production, metadata, or book rights deals (use publishing). The blurb, retailer description, and the rights a short-fiction market buys, such as reprint rights, stay here.
---

# Submission

## Overview

Get a finished manuscript out the door. This skill checks submission
readiness, drafts the submission package (query letter, pitch, synopsis,
blurb, comp titles), builds the manuscript in submission format, and keeps a
tracker of where the book has gone. Package files live under `submission/`
in the story project. The author sends every submission themselves; this
skill prepares materials and records outcomes.

## Prerequisites

A story project with a complete or near-complete draft. Verify `story.md`
exists in the project root and read its `status`, `genre`, `sub-genre`,
`premise`, `author` (or `authors` for a co-written book), `contact`, and `language` fields. If `status` is not `complete` or
`revising`, tell the user the package can be drafted now but the readiness
check will fail until the draft is finished.

## Language And Market

`language` (a missing field means `en`) is the book's language. Ask which
market the user is submitting to. The query letter, Shunn manuscript
format, comp conventions, and word-count norms in the references are the
English-language (mainly US and UK) market's. Other markets have their
own practice: some publishers take submissions directly rather than
through agents, and many ask for a synopsis and sample pages in their own
format. Ask the user for the guidelines of the agents or publishers they
are targeting and follow those; never present English-market conventions
as universal. Write the package in the language the agent or publisher
reads, which is usually the book's.

## When to Use

- Checking whether a manuscript is ready to submit
- Drafting or revising a query letter, pitch, synopsis, blurb, or comp list
- Building a Shunn-format manuscript for agents or magazines
- Writing a retailer or back-cover description for self-publishing
- Recording queries sent and responses received
- Submitting short fiction to magazines, anthologies, or contests:
  simultaneous or exclusive submissions, rights, response windows, and
  status queries
- Choosing and ordering the stories for a collection, and its
  previously-published acknowledgements
- NOT for self-publishing production (ISBNs, retailer metadata, print
  interiors, launch, rights deals and contracts): use the `publishing`
  skill. This skill still drafts the blurb and retailer description it
  uses, and records the rights a short-fiction market buys
- NOT for pitching a series of several books or writing its series overview
  (use `series-continuity`); the query for book one is still drafted here
- NOT for revising the manuscript itself (use `revision-continuity`)
- NOT for reader feedback rounds (use `feedback-triage`)

## Hard Rules

- Never invent the author's bio, credentials, awards, publication history,
  platform, or contact details. Ask the user, or leave a clearly marked
  `[TODO: author to supply]` placeholder.
- Never invent agent, publisher, or market names, submission guidelines,
  pay rates, rights terms, response times, dates, or responses. Tracker
  entries come from the user.
- Never send, email, or upload anything. The user submits.
- Never claim sales figures, bestseller status, awards, or endorsements for
  comp titles or the author that the user has not confirmed.
- Package copy describes the book as written. Read the manuscript and the
  bible; do not promise events, tone, or an ending the draft does not
  deliver.

## Workflow

### 1. Readiness check

Run the deterministic checks and report every finding before drafting:

```shell
story reindex .
story wordcount . --write
story check .
story prose .
story report .
```

Then check what the CLI cannot:

1. `story check .` (validate, links, and continuity) has no errors. List
   warnings for the user to accept or fix.
2. `story prose .` shows no avoided spellings, and the user has reviewed
   the other findings. If `style-sheet.md` is missing or still the
   scaffold, suggest the `voice-style` skill first.
3. Every chapter has `status: revised`, `final`, or `complete`. List any
   still at `outline` or `draft`.
4. The total word count sits inside the range for the category in
   `references/word-count-norms.md`. Those ranges are rough conventions
   for the English-language market only: state the number and the range,
   and ask the user to confirm current norms for their market. For a book
   in another language, report the count and ask for that market's norms
   instead. A Chinese or Japanese book is counted in characters: report
   `story wordcount .`'s character total, and `story validate .` checks
   `target-characters` against per-form character ranges where a source
   sets one. Never pad or cut to hit a number without the user's direction.
   When the count is well outside the range and the user wants to change
   it, hand the book to `revision-continuity`'s length pass
   ([`../revision-continuity/references/pass-checklists.md#length-pass`](../revision-continuity/references/pass-checklists.md#length-pass)),
   which budgets the cut or expansion by chapter and arc instead of
   trimming every chapter evenly.
5. No `[TODO` markers remain in chapter prose. `story validate` warns about
   each chapter that still has one.
6. Open questions and planted promises are resolved, or deliberately left
   for a sequel (check `story.md` `precedes`). Once `story.md` is
   `status: complete`, every open question and planned or planted promise
   or clue is a `story continuity` error, which fails the story-checks CI.
   No status means "pays off in the next book", so for each thread the
   user confirms is left for a sequel, add an entry to
   `continuity/exemptions.md` rather than changing its status:

   ```yaml
   ---
   type: exemption-log
   exemptions:
     - code: complete-with-open-promise
       pattern: "continuity/promises/the-sealed-letter.md is still planted"
       reason: "Pays off in book two."
   ---
   ```

   Rerun `story continuity .` and confirm the finding shows as `dismissed`.

Give a verdict: `ready`, `ready-with-caveats` (list them), or `not-ready`
(list the blockers and hand them to `revision-continuity`).

### 2. Pitch and logline

1. Read `story.md` (premise, synopsis), the main arc files, and the
   protagonist's character file.
2. Draft a one-sentence pitch: protagonist + goal + obstacle + stakes, in
   under 35 words. `../story-init/references/title-logline.md` has the
   logline recipe.
3. Offer two or three variants; the user picks. Save the chosen pitch at
   the top of `submission/query.md`.

### 3. Comp titles

Follow `references/comp-titles.md`. Propose candidates with a one-line
reason each, mark every one unverified until the user confirms year,
category, and fit, and save the agreed list to `submission/comps.md`.

### 4. Query letter

Follow `references/query-letter.md`. Draft `submission/query.md` with the
hook, one or two book paragraphs, the metadata line (title, genre, word
count rounded to the nearest thousand, comps), and a bio placeholder the
author fills in. Keep the letter between 250 and 350 words. If the user
names a specific agent, add a personalization line only from facts the user
provides.

### 5. Synopsis

1. Generate the mechanical draft:

   ```shell
   story synopsis . --pages 1 --out submission/synopsis-1-page.md
   story synopsis . --pages 3 --out submission/synopsis-3-page.md
   ```

2. The CLI output is a scaffold stitched from the `story.md` synopsis and
   each arc's Setup, Rising Action, Climax, and Resolution sections.
   Rewrite it into polished prose: present tense, third person, main
   characters' names in capitals on first use, every major turn, and the
   ending revealed. Agents expect the ending; never withhold it.
3. Keep the 1-page version near 500 words and the 3-page version near
   1,500. Overwrite the generated files with the rewritten versions and add
   the frontmatter from Conventions below.
4. If the output is thin, the arc files are thin: fill the missing arc
   sections with the `plot-structure` skill, rerun, then rewrite. `--out`
   never replaces an existing file in `submission/`, so to rerun, write to
   `dist/` and merge, or delete the generated file first after checking with
   the user that it holds no rewriting they want to keep.

### 6. Blurb and retailer description

Follow `references/blurb.md`. Draft `submission/blurb.md` with a tagline,
the back-cover copy (150-200 words), and, for self-publishing, a retailer
description with the same copy plus a comp line if the user wants one. The
blurb never reveals the ending.

This skill owns the retailer description: `submission/blurb.md` is its
only draft, and the `publishing` skill reads it there. Keep it and the
`description` field in `story.md` in step when the user self-publishes.

### 7. Build the manuscript

For agents and short-fiction markets, build Shunn manuscript format:

```shell
story build . --format docx --shunn
story build . --format shunn
```

These write `dist/<story-id>.shunn.docx` and `dist/<story-id>.shunn.md`.
The DOCX has a running head on every page after the first: the author's
surname, a short title, and the page number (`Writer / The Last Ember / 2`).
The build takes the last word of the first author's name (the first word
in a Chinese, Japanese, Korean, or Hungarian book) and the title before
any subtitle, and cuts a long one to fit. When either is wrong, such as
`Le Guin`, set `surname` or `short-title` in `story.md`; the build uses
them whole.
For a market that takes PDF, add `--pdf` to the `shunn` build: it renders
`dist/<story-id>.shunn.pdf` (US Letter, Courier, double-spaced, running
head) with a paged-media engine the user has installed, and stops with
install hints when there is none.

The PDF and DOCX are US Letter, which North American markets expect. For a
market that asks for A4 (most outside North America), add `--paper a4` to
the `--pdf` or `docx --shunn` build; the 1-inch margins stay. Go by the
market's guidelines, not the author's language or country. An author who
always submits on A4 can set `paper: a4` under a `build` entry in
`cli-defaults` in `story.md`; other builds ignore it.

Confirm `story.md` has `author` (or `authors`) and `contact` first; the
title page uses them, joining co-authors with "and". Shunn builds leave out `matter/` pages, as submissions expect. With
`form: short-story` or `form: flash` in `story.md` they use Shunn's
short-story layout: the text runs on from the title block, chapters become
sections separated by a centred `#`, and there are no chapter headings or
page breaks. Any other form starts each chapter on a new page. For
self-publishing, hand off to the `publishing` skill, which covers EPUB and
print builds (`story build . --format epub`, `--format print --trim 6x9`),
retailer metadata, and launch.

For a one-page metadata sheet to check the pitch facts against (title,
series, author, word count, description length against retailer limits,
keywords, BISAC subjects, and missing fields), run:

```shell
story build . --format metadata
```

If `story.md` has an `ai-disclosure`, check each agent's or market's
policy on AI-assisted work and disclose as they require; see the
`editorial-review` skill.
Tell the user which file in `dist/` to send, and remind them to check each
agent's or market's guidelines for format and attachment rules.

### 8. Track submissions

Create `submission/tracker.md` from `references/tracker-template.md` the
first time the user reports sending a submission. Add or update a row each
time the user reports a submission or a response, using only what they tell
you. On request, summarize: queries out, partial and full requests, offers,
declines, and entries with no response after the window the user sets.

### 9. Short fiction and collections

For a short story, novelette, or novella going to magazines, anthologies,
or contests, follow `references/short-fiction-markets.md` instead of steps
2 to 6: the story goes out in full with a short cover letter. Use the
short-fiction tracker columns (submission type, rights offered) and the
publication history section from that reference, and check the tracker
before suggesting a market: a story with an open exclusive submission goes
nowhere else, and an exclusive market needs a story with no open
submissions. For a market that reads anonymously, add `--anonymous` to the Shunn
build, which leaves out every name, the running head's surname included.
To assemble a collection, follow its "Assemble a collection" section:
choose the stories, find the linking threads, propose an order, and draft
the acknowledgements from the publication history.

## Conventions

- Package files: `submission/query.md`, `submission/comps.md`,
  `submission/synopsis-1-page.md`, `submission/synopsis-3-page.md`,
  `submission/blurb.md`, `submission/tracker.md`.
- Each file has YAML frontmatter with a `type` (`query`, `comps`,
  `synopsis`, `blurb`, `submission-tracker`) and `updated: YYYY-MM-DD`.
- `submission/` is outside the story model: the CLI does not validate it
  and builds never include it.
- Word counts in submission copy come from `story wordcount .`, rounded to
  the nearest thousand (`87,000 words`). A Chinese or Japanese book gives
  its length in characters, as `story wordcount .` reports it (`12万字`,
  or sheets of 400字 when a Japanese contest asks for them).
- Tracker statuses: `queried`, `requested-partial`, `requested-full`,
  `offer`, `declined`, `no-response`, `withdrawn`, plus `submitted` and
  `held` for short fiction.
- When the manuscript changes after the package is drafted, reread the
  package and update anything the revision made untrue.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, perform the readiness checks manually and write the synopsis from the arc files.

After the readiness check, or any manuscript change made for submission:

```shell
story reindex .
story wordcount . --write
story check .
story prose .
```

## Reference Files

- **`references/query-letter.md`** - Query structure (hook, book paragraphs, metadata line, bio), length, personalization, and common mistakes
- **`references/blurb.md`** - Back-cover and retailer description formulas for genre fiction, length, and taglines
- **`references/comp-titles.md`** - How to choose comparable titles, how to phrase them, and the verification rule
- **`references/word-count-norms.md`** - Rough word-count ranges by category for the English-language market only, to confirm with the user
- **`references/tracker-template.md`** - `submission/tracker.md` template and status definitions
- **`references/short-fiction-markets.md`** - Magazine, anthology, and contest submissions (simultaneous and exclusive, rights, response times and status queries, tracker columns, publication history) and assembling a story collection

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
