---
name: adaptation
description: This skill should be used when the user asks to "make an audiobook", "narration script", "narrator", "ACX", "Findaway", "pronunciation guide", "how long is the audiobook", "adapt to a screenplay", "Fountain", "screenplay", "picture book", "spreads", "illustration notes", "art notes", "comic script", "comics script", "graphic novel", "panels", "interactive edition", "turn the book into Ink or Twine", "translate the book", "translation", "foreign edition", "glossary for translators", or wants to turn a story project into another form or language, or to plan a picture book. NOT for writing a new branching or choose-your-own-adventure story (use interactive-fiction), or writing rhyming picture-book text (use verse-craft).
---

# Adaptation

## Overview

Turn a story project into another form: an audiobook narration script, a
screenplay in Fountain, a picture-book pagination plan, a comics script, an
interactive-fiction branch map, or an edition in another language. The
story project stays the source of truth. Adaptation files live in
`adaptations/` inside the project, except translations, which become their
own project folder with the same ids.

## Prerequisites

A story project with `story.md` in the root and chapters drafted far
enough to adapt. Read `story.md` (`title`, `form`, `language`, `status`),
the chapter and scene records, and the character, location, and glossary
files the adaptation touches. Adapting a draft that is still changing means
redoing the adaptation; say so if `status` is not `revising` or `complete`.

## When to Use

- Producing an audiobook: narration script, runtime estimate,
  pronunciation guide, narrator and production checklist
- Adapting the story to a screenplay, comics script, or interactive
  edition (a linear book turned into Ink or Twine)
- Planning or drafting a picture book (`form: picture-book`)
- Translating the book, or preparing a glossary and style sheet for a
  translator
- NOT for publishing metadata, print, ebook, launch, or rights deals (use
  `publishing`); audio and film rights one-sheets live there
- NOT for query letters or agent submission (use `submission`)
- NOT for new prose in the source book (use `chapter-writing`)
- NOT for writing a book that branches from the start, such as a new
  choose-your-own-adventure story (use `interactive-fiction`)
- NOT for writing or scanning verse, including rhyming picture-book text
  (use `verse-craft`)
- Nonfiction and poetry collections are outside the story project model.
  The CLI checks fiction entities (characters, chapters, scenes,
  continuity); do not force a poetry collection or nonfiction book into
  it. A short-story collection does fit: see `docs/series.md`, Short-story
  collections and anthologies.

## Hard Rules

- Never change the source manuscript to suit an adaptation without the
  author's approval. Adaptation choices live in `adaptations/`.
- Do not put adaptation `.md` files in the project root: any root `.md`
  other than `story.md`, `style-sheet.md`, and `progress.md` is reported as
  a stray file. Use `adaptations/` or a non-`.md` extension such as
  `.fountain`.
- Never invent a pronunciation for a real place, person, or language.
  Ask the author or cite a source.
- Retailer and audio-platform specs change. Give the working figures and
  tell the author to check the platform's current spec.
- Contracts and royalty terms for narrators, illustrators, and translators
  are not legal advice; point to the `publishing` skill's contract checklist
  and a professional.

## Workflow

### 1. Audiobook

Follow `references/audiobook.md`.

1. Add `pronunciation` to every character, location, faction, artifact, and
   glossary term a narrator could say wrong (`pronunciation: SEER-sha`).
   Respell for the narrator's language, not always English. Ask the
   author for any they have not decided.
2. Build the script:

   ```shell
   story build . --format narration --out adaptations/audiobook/narration-script.md
   ```

   It opens with the pronunciation guide table, then each chapter with its
   estimated finished runtime, scene breaks as `[pause]`, and the total
   runtime. The rate comes from the book's `language` (155 words per
   minute in English; the script's first line names it), and the credits
   are in that language; time a sample chapter and rescale (see
   `references/audiobook.md`). `--out` never replaces an existing
   file under `adaptations/`, so delete the old script before a rebuild.
3. Review the script for what reads badly aloud: long dialogue runs
   without tags, visual-only jokes, footnotes, maps, letters and texts,
   tables. Record fixes as narrator notes in
   `adaptations/audiobook/production.md`; change the manuscript only with
   the author's approval.
4. Draft the production checklist from the reference: route (ACX,
   Findaway Voices by Spotify, other), narrator audition script, retail
   sample, chapter file list, credits, and AI narration disclosure.

### 2. Screenplay (Fountain)

Follow `references/fountain.md`.

1. Add `setting: interior`, `exterior`, or `both` to each location the
   scenes use, and to any scene whose place differs from its location's
   (on the harbor wall, not in the harbor office). Ask the author when the
   prose does not settle it. Run `story validate .`.
2. Build the scene list from scene records (reading order, or
   `story timeline .` for story-time order). Each scene becomes one or
   more sluglines from its `location`, `setting`, `time`, and
   `characters`.
3. Mark each scene keep, merge, cut, or externalize (interior moments that
   need an action or line). Save it as
   `adaptations/screenplay/scene-list.md`.
4. Start the script from the scene records:

   ```shell
   story build . --format fountain --out adaptations/screenplay/{story-id}.fountain
   ```

   It writes a title page, a `##` section per chapter, and one scene
   heading per scene record with the source scene id, cast, and scene
   notes as unprinted `[[...]]` notes. It carries no prose: the build
   cannot adapt, so every line of action and dialogue is yours to write.
   A forced heading (`.LAMP ROOM - DUSK`) means the scene and its location
   have no `setting`; fix the record or the heading. `--out` never
   replaces an existing file under `adaptations/`, so once the script is
   drafted, build to `dist/` instead to compare a new skeleton with it.
5. Apply the scene list's decisions to the skeleton, then draft act by
   act and check length at about one page per minute. Keep each scene's
   `[[Source: ...]]` note.

### 3. Picture book

Follow `references/picture-book.md`.

1. Set `form: picture-book` in `story.md`, or start a new project with
   `story init 'Title' --form picture-book` (target 500 words).
2. Make the pagination plan in `adaptations/picture-book/pagination.md`:
   32 pages, 14 spreads of story, a page-turn beat on each spread.
3. Keep the text in chapters, one chapter per spread, and the
   illustration briefs and art notes in the plan, not the prose (text in a
   chapter is counted and ships in every build). Give each spread one
   scene record and a `hook` for its page-turn beat, and set `story.md`
   to `status: revising` once all spreads are drafted; see "Spreads And
   The CLI Checks" in the reference for the warnings this clears.

### 4. Comics or graphic novel script

Follow `references/comics-script.md`. Break the story into pages
(`adaptations/comics/page-plan.md`), then write the full script with pages,
panels, captions, balloons, and SFX in
`adaptations/comics/{issue-or-part}.md`.

### 5. Interactive fiction

Follow `references/interactive-fiction.md`. Map the linear scenes to nodes,
choose a branching structure with the author, and record the branch map in
`adaptations/interactive/branch-map.md`.
Once the interactive edition project exists, draft and revise its chapters
with the `interactive-fiction` skill.

- **Twine:** make the interactive edition its own project (copy the
  source project without `dist/`, as for a translation), one chapter per
  passage, with `choices` frontmatter (`text` and `to`) on each chapter
  that branches. Check and build it:

  ```shell
  story reindex .
  story wordcount . --write
  story check .
  story build . --format twee --out adaptations/interactive/{story-id}.twee
  ```

  Fix every `unreachable-chapter` warning about a chapter no choice path
  reaches.
  `--out` never replaces an existing file under `adaptations/`, so delete
  the old `.twee` before a rebuild.
- **Ink:** set up the interactive edition project the same way, check it
  with the same commands, and build it:

  ```shell
  story build . --format ink --out adaptations/interactive/{story-id}.ink
  ```

  Open the `.ink` file in Inky, or compile it with `inklecate`. The build
  escapes ink syntax in chapter prose, so write ink state (`VAR`, `~`,
  `{ }`) by hand in the built file, and only once the branch structure is
  settled: `--out` never replaces an existing file, and a rebuild after
  changing `choices` means deleting the old `.ink` and carrying the
  hand-written logic into the new one. Ask the author before deleting a
  file that has hand-written logic in it.

### 6. Translation

Follow `references/translation.md`.

1. Prepare the term base: add a `## Translations` section to each glossary
   term, and `pronunciation` where it helps. Check new translated names
   with `story names`.
2. Copy the source project to a new folder (without `dist/`), set
   `language`, remove `series`, `book-number`, `follows`, and `precedes`
   from the copied `story.md`, and keep every id as the English
   kebab-case id.
3. Write a style sheet for the target language in the new project.
4. After translation, run the checks in both projects and compare the
   chapter sets:

   ```shell
   story reindex ../book-es
   story wordcount ../book-es --write
   story check ../book-es
   story compare ../book-es --against .
   ```

## Conventions

- Adaptation files: `adaptations/audiobook/`, `adaptations/screenplay/`,
  `adaptations/picture-book/`, `adaptations/comics/`,
  `adaptations/interactive/`. The CLI does not validate them and builds
  never include them.
- Markdown planning files carry frontmatter with a `type`
  (`audiobook-production`, `scene-list`, `pagination-plan`, `page-plan`,
  `branch-map`, `translation-notes`) and `updated: YYYY-MM-DD`.
- Scenes, characters, and locations keep their story ids in every
  adaptation file, so each adapted scene traces back to its source.
- `pronunciation` is plain respelling in capitals for the stressed
  syllable (`SEER-sha`, `kah-LEE-na`), not IPA, unless the narrator asks
  for IPA.
- A translated edition is a separate story project with the same ids and
  its own `language`, `isbn`, and metadata. Its `story.md` has no
  `series`, `book-number`, `follows`, or `precedes`; those are for
  different books, and copied values break `story links` and
  `story series`.
- When the source manuscript changes, list the adaptation files the change
  affects and update them.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, write the narration script and scene lists by hand from the chapter and scene files.

After adding `pronunciation`, `setting`, or glossary translations, or
setting `form` or `language`:

```shell
story reindex .
story wordcount . --write
story check .
```

Run the same block after changing chapters in a picture-book, translated,
or interactive project. After adding, retargeting, or removing `choices`,
run it and rebuild the Twee or ink file.
`story move` and `story remove` keep `choices` targets in step.

## Reference Files

- **`references/audiobook.md`** - Narration script review, pronunciation, runtime, production routes, narrator auditions, audio file checklist, and AI narration disclosure
- **`references/fountain.md`** - Scene-list-from-scene-records method, novel-to-screen choices, and Fountain syntax
- **`references/picture-book.md`** - 32-page and 14-spread pagination, page-turn beats, text and illustration interplay, spread brief template, and art notes
- **`references/comics-script.md`** - Page and panel script format, pacing per page, balloon limits, and page-turn reveals
- **`references/interactive-fiction.md`** - Branch maps from scenes, branching structures, state, chapter `choices` and the Twee and ink builds, and Ink and Twine syntax
- **`references/translation.md`** - Glossary as term base, per-language style sheets, name decisions, and continuity across language editions

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
