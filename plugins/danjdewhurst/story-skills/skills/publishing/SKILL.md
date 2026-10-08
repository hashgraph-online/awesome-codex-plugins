---
name: publishing
description: This skill should be used when the user asks to "self-publish", "publish my book", "ISBN", "copyright page", "book metadata", "BISAC", "keywords", "KDP", "IngramSpark", "Draft2Digital", "go wide", "Kindle Unlimited", "print interior", "trim size", "paperback", "ebook", "EPUB", "cover wrap", "spine width", "pricing", "launch plan", "ARC team", "advance readers", "newsletter", "reader magnet", "Amazon ads", "BookBub", "rights", "foreign rights", "audio rights", "film rights", "publishing contract", or wants to take a finished manuscript through production, distribution, launch, and rights management. It owns contracts and rights sales; NOT for permission to quote lyrics, epigraphs, or other material in the book (use editorial-review), or for drafting the blurb or retailer description (use submission).
---

# Publishing

## Overview

Take a final manuscript into readers' hands. This skill fills the
publishing metadata in `story.md`, writes the copyright page, builds and
checks the ebook and print interior, walks the author through
distribution, pricing, and launch, and keeps an inventory of the rights
the author holds. Planning files live under `publishing/` in the story
project. The author makes every account, upload, purchase, payment, and
signature; this skill prepares, checks, and records.

## Prerequisites

A story project whose manuscript is final or nearly so. Verify `story.md`
exists and read `title`, `status`, `author` or `authors`, `genre`,
`series`, `book-number`, `cover`, and any publishing fields already set. If
`status` is not `complete`, say that metadata and launch planning can start
now but the files must be rebuilt after the last revision.

## Language And Market

Read `language` in `story.md` (a missing field means `en`) and ask which
countries the author is publishing in. The book's language decides the
language of the description, keywords, and copyright page; the market
decides the ISBN agency, subject schemes, retailers, and pricing rules.
The references start from the US and UK English-language market and
note the rest: Thema subjects and ISBN agencies elsewhere in
`references/metadata-checklist.md`, other retail routes and fixed book
prices in `references/launch-plan.md`, and rights by language and
territory in `references/rights-one-sheet.md`. Never assume a US retailer, scheme, or
law applies elsewhere; say what to check.

## When to Use

- Filling retailer metadata: ISBN, publisher, date, description, keywords,
  BISAC and Thema subjects, language, cover alt text, AI disclosure
- Writing the copyright page or checking epigraph and lyric permissions
- Building and checking the EPUB or the print interior; choosing trim size
- Choosing retailers and exclusivity, setting prices, planning a launch
- Recording rights, reviewing a contract offer, drafting a rights one-sheet
- NOT for query letters, agent submission, synopsis, blurb, or retailer
  description drafting (use `submission`; this skill reuses its blurb and
  retailer description)
- NOT for audiobook scripts, screenplays, translations, or other formats
  (use `adaptation`)
- NOT for revising the manuscript (use `revision-continuity`)

## Hard Rules

- Never invent an ISBN, publisher or imprint name, publication date, price,
  review, endorsement, sales figure, award, or bestseller claim. Ask, or
  leave a `[TODO: author to supply]` placeholder.
- Never assert current retailer specs, royalty rates, or fees as fact.
  They change. Give the working figure as a starting point and tell the
  author to check the retailer's current spec before relying on it.
- Legal, tax, and contract matters are **not legal or tax advice**. Flag
  issues, explain why they matter, and recommend an agent, a publishing
  lawyer, an accountant, or an author organization's contract-vetting
  service.
- Never create accounts, upload, buy, sign, or send. The author does.
- `ai-disclosure` must say what actually happened. Ask the author how AI
  tools were used; never minimise it.

## Workflow

### 1. Readiness

```shell
story reindex .
story wordcount . --write
story check .
story prose .
story build . --format metadata
```

The metadata sheet lists every missing field in its readiness checklist,
including a `Permissions cleared for quoted matter` row that names each
matter page still at `permission: pending`, whatever the story status,
a `No [TODO markers in chapter prose` row that names each chapter still
holding a `[TODO` marker, which every build would print, and a
`No [TODO markers on matter pages` row that names each matter page still
holding one, such as a `[TODO: author to supply]` ISBN line. Report the
checklist with the validate findings, and any `has no prose yet` warning from the build: that
chapter would ship as a heading-only page, so ask whether to write it or
remove it. `validate` warns about
`permission: pending` only once the story `status` is `complete`, and
about a research note with a `risk` but no `reviewed-by` only when a final
or complete chapter uses it, so also list them directly before
publication:

```shell
story list matter --where permission=pending
story list research --where risk --where '!reviewed-by'
```

Report every pending permission, and every risky note without
`reviewed-by`, whatever the chapter status. If `story passes .` shows unfinished revision passes, say so
before production starts.

`story export` and every build that prints matter pages (markdown, EPUB,
DOCX, HTML, print, narration) leave out a page whose `permission` is
`pending`, misspelt, or any value but `not-needed`, `granted`, or
`public-domain`, and warn `permission-pending-left-out` for it, so a file built
for upload, a printer, or readers never carries the uncleared quote.
Report each such warning: the book builds without that page until the
author confirms the permission. Add `--include-pending` only when the
author asks to see the page in a proof they read alone, such as a print
PDF for layout, and tell them not to share or upload that file. Never add
it to a build for a retailer, a printer, advance readers, or the review
copy workflow, and never set it in `cli-defaults` (validate refuses it).

### 2. Metadata

Fill the `story.md` fields with `references/metadata-checklist.md`:
`isbn`, `publisher`, `publication-date`, `language`, `description`,
`keywords`, `subjects`, `copyright`, `cover-alt`, `ai-disclosure`, and
`authors` for co-written books, or `editor` for an anthology (each
story's writer then goes in its chapter's `author`). Take the description from
`submission/blurb.md` (the `submission` skill drafts and owns it; draft
it there first if it is missing).
Write the description and keywords in the book's language. `subjects`
holds BISAC codes only; when the author's distributors ask for Thema,
choose the codes from the checklist and record them in
`publishing/launch-plan.md`.
Rebuild the sheet and repeat until the checklist is clean:

```shell
story reindex .
story wordcount . --write
story check .
story build . --format metadata
```

### 3. ISBNs and copyright page

1. Explain the ISBN choices in `references/metadata-checklist.md`: one
   ISBN per format and edition, who issues them in the author's country
   (outside the English-speaking markets too), and the trade-offs of a
   free retailer ISBN. Record the ebook or print
   ISBN the author supplies in `isbn`.
2. Create the copyright page and fill it from
   `references/copyright-page.md`:

   ```shell
   story add matter 'Copyright' --order 0 --heading=false
   ```

   Use an `order` lower than every other front page so it sits first
   (behind the title page); `story add matter` otherwise takes the next
   free number. `--heading=false` writes `heading: false` (on an existing
   page, edit its `heading:` key rather than adding a second one). Without this page, every build
   except Shunn generates a minimal one from `copyright`; write it by hand when the book needs credits, permissions,
   or a Library of Congress line. Leave `[TODO: author to supply]` on any
   line the author has not given you, such as an ISBN not yet bought.
   `validate` warns about it (`matter-todo-markers`), and so does every
   build that prints the page, while still building it. Ask the author
   for each such line, and tell them not to upload a file built while
   that warning shows. Promote the code to `level: error` under `severity`
   in `story.md` only when the author asks for release builds to fail on it.
3. For each epigraph, lyric, or quoted page in `matter/`, set `permission`
   (`not-needed`, `pending`, `granted`, `public-domain`), `rights-holder`,
   and `credit`. Quoting song lyrics almost always needs permission.

### 4. Ebook

First agree the look of the ebook, review copy, and print interior with
the author. Without a `build-style` block in `story.md` they keep the
classic look (Georgia, centred headings, indented paragraphs, `* * *`
scene breaks). To change it, add one entry, for example:

```yaml
build-style:
  - preset: elegant
    scene-break: "~"
```

`preset` is `classic`, `modern`, or `elegant`; `body-font`,
`heading-font`, `heading-style`, `scene-break`, `drop-caps`, and
`paragraphs` override it, and `css` adds a `.css` file from the project.
Never set a font the author has not chosen, and remind them that an
ebook reader can replace the fonts. The Shunn manuscript and DOCX builds
ignore the block. Run `story validate` after editing it: a bad value
stops the EPUB, HTML, and print builds.

```shell
story build . --format epub
```

The EPUB carries accessibility metadata, language, semantic chapter and
matter markup, a landmarks nav, the cover with `cover-alt`, and the
metadata fields. If the author has EPUBCheck or Ace by DAISY installed,
run them on the file in `dist/` (`java -jar epubcheck.jar <file>.epub`,
`ace <file>.epub`) and fix errors before upload. Ask the author to open it
in at least one reading app and in the retailer's previewer.

### 5. Print interior

Follow `references/print-interior.md`:

1. Choose the trim size with the author (`5x8`, `5.25x8`, `5.5x8.5`, `6x9`,
   `a5`), then build:

   ```shell
   story build . --format print --trim 6x9
   ```

2. Render the PDF. If the author has a paged-media engine installed
   (Prince, WeasyPrint, `pagedjs-cli`, or Chrome as a fallback), let the CLI
   find and run it:

   ```shell
   story build . --format print --trim 6x9 --pdf
   ```

   It writes `dist/<story-id>.pdf`. Name an engine with
   `--pdf-engine <name|path>`. With none installed it stops (exit 4) and lists
   what to install; the CLI bundles none.
3. Check the rendered PDF against the printer's file requirements; use its
   actual page count for the cover.
4. Tell the author to get the spine width and full cover wrap template from
   the printer's cover calculator, and to order a printed proof before
   release.

### 6. Distribution and pricing

Lay out the options in `references/launch-plan.md`: KDP, IngramSpark,
Draft2Digital or another aggregator, and direct sales, plus the trade-off
between exclusivity (KDP Select and Kindle Unlimited) and going wide.
For a book sold outside the US and UK, or not in English, add the routes
and fixed-price rules in its Outside the US and UK section. The
author decides; record the choices in `publishing/launch-plan.md`. Discuss
pricing with the considerations in the same reference, not a formula.

### 7. Retailer page copy

The retailer description has one draft, in `submission/blurb.md`, and
the `submission` skill owns it: make any change there with that skill.
Check its first two lines, which show before "read more", and its length
against the metadata sheet's character count. Draft into
`publishing/retailer-copy.md` only series-page copy when `series` is set,
and A+ or enhanced-content ideas (a comparison chart of series books, a
character or map panel, a mood image with a quote), following
`../submission/references/blurb.md`.

### 8. Launch

Build `publishing/launch-plan.md` from the T-90 to T+30 timeline in
`references/launch-plan.md`: ARC team, newsletter and reader magnet, street
team, preorder, launch week, and paid ads with a test budget and stop
rules. Update the plan as the author reports what happened; never fill in
results they did not give you.

### 9. Rights and contracts

1. Keep `publishing/rights.md` from the inventory in
   `references/rights-one-sheet.md`: every right (print, ebook, audio,
   translation by language or territory, film and TV, and the rest), who
   holds it, the term, and the reversion terms. The original-language
   rows use the book's own language, not English by default.
2. When the author has a contract offer, read it against
   `references/contract-red-flags.md` and list each clause that matches a
   red flag with the question to ask. State that this is not legal advice
   and recommend a lawyer or agent before signing.
3. For rights the author wants to license, draft a one-sheet from
   `references/rights-one-sheet.md`.

## Conventions

- Planning files: `publishing/launch-plan.md`,
  `publishing/retailer-copy.md`, `publishing/rights.md`,
  `publishing/one-sheet-{right}.md` (for example
  `publishing/one-sheet-audio.md`).
- Each file has YAML frontmatter with a `type` (`launch-plan`,
  `retailer-copy`, `rights-inventory`, `rights-one-sheet`) and
  `updated: YYYY-MM-DD`.
- `publishing/` is outside the story model: the CLI does not validate it
  and builds never include it. Build output in `dist/` is disposable;
  rebuild it rather than editing it.
- One `story.md` holds one edition's metadata. When the ebook and print
  ISBNs differ, record the one being built in `isbn`, set it before each
  build, and keep both in the copyright page and `publishing/rights.md`.
- Dates are `YYYY-MM-DD`. Word counts come from `story wordcount .`.
- After any manuscript change, rebuild every format and recheck page count
  and spine width before re-uploading.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, fill the metadata by hand from `references/metadata-checklist.md` and tell the user that the EPUB, print, and metadata builds need the CLI.

After editing `story.md` metadata, adding matter pages, or changing the
manuscript:

```shell
story reindex .
story wordcount . --write
story check .
story build . --format metadata
```

## Reference Files

- **`references/metadata-checklist.md`** - Every publishing field, ISBN agencies and trade-offs, keywords, BISAC and Thema subjects, descriptions, AI disclosure, and CIP or PCN notes
- **`references/copyright-page.md`** - Copyright page template, optional lines, permissions credits, and legal deposit notes
- **`references/print-interior.md`** - Trim size choice, page-count estimates, rendering to PDF, printer checks, cover wrap, and proofs
- **`references/launch-plan.md`** - Distribution and exclusivity, routes outside the US and UK, pricing considerations including fixed book prices, and the T-90 to T+30 launch timeline with ARCs, newsletter, and ad testing
- **`references/contract-red-flags.md`** - Clause-by-clause red flags for publishing and rights contracts, and where to get a professional review
- **`references/rights-one-sheet.md`** - Rights inventory template by language and territory, and one-sheets for foreign, audio, and film rights

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
