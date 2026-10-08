---
name: line-editing
description: This skill should be used when the user asks to "line edit", "edit my prose", "polish this chapter", "tighten the prose", "improve the sentences", "copyedit", "proofread", "proof pass", "check grammar and punctuation", "dialogue punctuation", "make the voices distinct", "everyone sounds the same", "read it aloud", "read-aloud pass", "text to speech", or wants a sentence-level quality pass on drafted chapters that preserves the author's voice. NOT for creating the style sheet, recording character voices, or checking voice consistency (use voice-style).
---

# Line Editing

## Overview

Own the prose-quality passes that come after structure is settled: the
line edit (sentence clarity, rhythm, precision, voice), character-voice
differentiation, the copyedit against `style-sheet.md`, a read-aloud pass,
and a proof pass on a built copy. Every change is proposed with a
before/after and a one-line rationale so the author can accept or reject
it. The author's voice is the standard, not the agent's taste. The
`better-writing` skill, when installed, is an optional complement for
anti-generic checks; this skill does not depend on it.

## Prerequisites

A story project with `story.md` and drafted chapters (status `draft` or
later). Read `style-sheet.md` if present; if it is missing or thin, build
it first with the `voice-style` skill, because the copyedit checks against
it.

## Language

Read `language` in `story.md` (a BCP 47 tag such as `en-GB`, `fr`, or
`ja`; a missing field means `en`). Edit in that language and to its
grammar and conventions, and write edit notes in the language the user
works in with you, quoting the prose exactly as written. The checklists'
word-level advice (filter words, -ly adverbs, *said*, dialogue
punctuation) is English: for another language, apply its aim, not its
word lists, and take dialogue and punctuation from the style sheet and
`references/language-conventions.md`. When `story prose` or
`story voices` reports a check skipped for the book's language, or a
check plainly does not fit it, do that pass by reading.

## When to Use

- A chapter's structure is settled and the prose needs polish
- Dialogue sounds the same from every speaker
- Preparing a manuscript for beta readers, an editor, or submission
- The `line`, `copyedit`, or `proof` revision pass is next in `story passes`
- NOT for structural, plot, or continuity revision (use `revision-continuity`; line-edit only after those passes, or the polish is wasted)
- NOT for setting house style, the voice description, or each character's recorded voice (use `voice-style`; this skill applies them)
- NOT for scene-level craft such as deep POV, subtext, or exposition strategy (use `scene-craft`)
- NOT for acting on external reader notes (use `feedback-triage`)
- NOT for writing or scanning verse (use `verse-craft`); this skill only
  flags rhymes that slipped into prose by accident

## Workflow

### 1. Scope and permission

1. Ask which chapters and which pass: line edit, voice differentiation,
   copyedit, read-aloud, or proof. Default order is the one below.
2. Ask how heavy the edit should be: **light** (errors and clear
   improvements only), **medium** (tighten and clarify), or **heavy**
   (restructure sentences and paragraphs). Default to light.
3. Never rewrite a passage wholesale without explicit permission. Propose
   edits; apply only what the author accepts, or apply all on explicit
   instruction.
4. Snapshot before a multi-chapter pass (see Draft Snapshots in the
   `revision-continuity` skill), and mark the pass in progress. If
   `story.md` has no `revision-passes` yet, `story passes . --init` writes
   the default ladder first; `story passes .` shows where the book is.

```shell
story passes . --start line
```

### 2. Line edit

1. Read `story.md` (POV, tense, Tone & Style), the style sheet's Voice
   section, and the chapter. Run `story prose .` for the chapter's counts.
   If the style sheet has no `samples`, suggest the author list an
   earlier book or chapter files they are happy with (see the `voice-style`
   skill), so the counts are measured against their own voice. A
   `prose-baseline-*` warning shows where a chapter drifts from it: use
   it to find passages to reread, and keep any drift the author meant.
2. Work paragraph by paragraph with `references/line-edit-checklist.md`:
   clarity, precision, economy, rhythm, POV distance, and voice.
3. Present edits in the format in `references/edit-note-format.md`:
   location, before, after, and one line of rationale. Group by
   paragraph; lead with the highest-impact changes; cap a batch at about
   20 so the author can review them.
4. Leave passages that are unusual but deliberate. When unsure whether a
   quirk is voice or error, ask.
5. To check a rewritten passage before putting it in the chapter, pipe it
   in: `story prose - < rewrite.md` lints it against the style sheet, and
   `story voices - < rewrite.md` checks its dialogue against the
   characters' `voice-avoid` lists.

### 3. Differentiate character voices

```shell
story voices .
```

The report fingerprints each character's attributed dialogue (sentence
length, contractions, questions, exclamations, signature words) and warns
when two voices are near-identical, when a character says a
`voice-avoid` word, and when a `voice-words` entry never appears.

1. For near-identical pairs, read both characters' Voice & Speech
   Patterns sections and propose line-level changes that follow them:
   vocabulary, sentence length, what each avoids saying, how each deflects.
   See the voice section of `references/line-edit-checklist.md`.
2. If a character file has no voice notes, propose `voice-words` and
   `voice-avoid` lists drawn from their best existing lines, and ask
   before adding them to the character file.
3. A line counts only when the narration names its speaker by a speech
   verb, or names one character in the paragraph. Pronoun tags
   (`she said`) and untagged lines are invisible to the report, so the
   POV character in close third is often under-counted; read those lines
   by hand, or name the tags in a sample chapter and rerun.
   `story voices --help` describes the command and, when
   `story-maintenance` is installed, the voices section of
   [`../story-maintenance/references/continuity-checks.md`](../story-maintenance/references/continuity-checks.md#voices)
   gives the full attribution rules and thresholds.

### 4. Copyedit

1. Mark the pass: `story passes . --start copyedit`.
2. Run `story prose .` and fix every avoided spelling. Then work through
   `references/copyedit-checklist.md` against `style-sheet.md`: grammar,
   punctuation, dialogue punctuation, capitalisation, hyphenation,
   numbers, and consistency of names and terms (check the glossary). For
   a book not in English, take dialogue and punctuation conventions from
   `references/language-conventions.md`; if the style sheet has not
   recorded them, settle them with the author first.
3. Record every new decision in `style-sheet.md` in the same change, so
   the next chapter follows it.
4. Tell the user plainly: this is a consistency and correctness pass, not
   a substitute for a professional copyeditor on a book going to print.

### 5. Read-aloud pass

Follow `references/read-aloud-guide.md`. Build the narration script:

```shell
story build . --format narration
```

Offer to play chapters with the system's text-to-speech if one is
installed (`say` on macOS; `espeak-ng` or `spd-say` on Linux). Check with
`command -v`; ask before installing anything. Choose a voice for the
book's `language` (`say -v '?'` and `espeak-ng --voices` list them); an
English voice reading another language is no test of the prose. Listen for stumbles,
unintended rhymes, tongue-twisters, and runs of same-length sentences;
record them as edit notes.

### 6. Proof pass

1. Mark the pass: `story passes . --start proof`.
2. Build the copy the reader will see:

```shell
story build . --format html
story build . --format print --trim 6x9
```

3. Proof against `references/copyedit-checklist.md`'s proof section:
   typos introduced by editing, doubled or missing words, broken scene
   breaks, chapter headings, matter pages, widows and orphans in the print
   copy. Cite locations by the HTML copy's paragraph anchors (`ch03-p12`).
4. To proof the print copy as a PDF, add `--pdf` to the print build:

   ```shell
   story build . --format print --trim 6x9 --pdf
   ```

   It finds and runs a paged-media engine the user has installed (Prince,
   WeasyPrint, `pagedjs-cli`, or Chrome as a fallback) and writes
   `dist/<story-id>.pdf`. Name an engine with `--pdf-engine <name|path>`.
   With none installed it stops (exit 4) and lists what to install; the
   CLI bundles none. Ask before installing anything.

### 7. Close the pass

1. Summarise what changed, what was kept on purpose, and any style-sheet
   or character-file updates.
2. Update chapter `status` only when the author agrees (`draft` to
   `revised`).
3. Mark the pass done, for example `story passes . --done line`, and run
   CLI Maintenance.

## Conventions

- The author's voice wins. Edit toward what the prose is already trying
  to do, not toward a generic "good prose" standard.
- One rationale line per change, naming the effect (*clearer subject*,
  *cuts a filter word*, *restores past tense*), never "sounds better".
- Edits are made directly in the chapter markdown, below `## Chapter
  Text`; never through a script that rewrites prose in bulk.
- Style decisions go in `style-sheet.md`; voice decisions about a
  character go in the character file (`voice-words`, `voice-avoid`, Voice
  & Speech Patterns), which stays canon.
- A line edit does not change events, facts, or who knows what. If an
  edit would, stop and hand it to `revision-continuity`.

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
available, apply the checklists by reading and keep word counts current by
hand.

After editing chapters, character voice fields, or the style sheet:

```shell
story reindex .
story wordcount . --write
story check .
story prose .
story voices .
```

## Reference Files

- **`references/line-edit-checklist.md`** - Paragraph-level line edit checks (clarity, precision, economy, rhythm, POV distance, voice) and character-voice differentiation levers
- **`references/copyedit-checklist.md`** - Copyedit and proof checks against the style sheet: grammar, punctuation, dialogue punctuation, consistency, and the proof pass on built copies
- **`references/read-aloud-guide.md`** - Running a read-aloud pass with the narration build and OS text-to-speech, and what to listen for
- **`references/language-conventions.md`** - Dialogue and punctuation conventions by language (quote marks, dialogue dashes, spacing before punctuation, Spanish ¿¡, CJK brackets), and how to record them in the style sheet
- **`references/edit-note-format.md`** - How to present edits to the author: before/after with rationale, batching, and recording accepted and rejected changes

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
