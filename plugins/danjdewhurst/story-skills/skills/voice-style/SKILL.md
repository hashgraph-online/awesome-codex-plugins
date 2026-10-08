---
name: voice-style
description: This skill should be used when the user asks to "create a style sheet", "style guide", "house style", "keep the voice consistent", "voice drift", "British or American spelling", "character voices", "lint the prose", "prose check", "filter words", "said-bookisms", "overused words", "repeated phrases", "similar character names", "voice fingerprints", or wants to record and enforce the voice and surface conventions of a story project. NOT for rewriting dialogue to make the voices distinct when everyone sounds the same (use line-editing), or a character's profile or arc (use character-management).
---

# Voice & Style

## Overview

Record the book's voice and surface conventions in `style-sheet.md`, then
enforce them. The style sheet is the copyeditor's record: dialect and
spelling choices, capitalisation, hyphenation, numbers, dialogue
punctuation, a one-line voice summary per major speaker, and a watch list.
Its frontmatter is machine-readable, and `story prose` counts violations
and prose tics in every chapter. Use this skill so voice stays the same
across chapters, drafting sessions, and agents.

## Prerequisites

A story project with `story.md` in the root. `story init` scaffolds
`style-sheet.md`; older projects can add it with `story init '<title>' --dir
. --force`, which only adds missing files, or by copying
`references/style-sheet-guide.md`'s frontmatter block by hand.

## Language

Read `language` in `story.md` (a BCP 47 tag; a missing field means `en`).
The style sheet records the conventions of that language, and the voice
description is written about prose in it. `dialect: british` and
`american` and the built-in word lists behind filter words, -ly adverbs,
and said-bookisms are English. For another language, set
`dialect: unspecified`, record spelling variants as `preferred` entries,
and settle dialogue and punctuation with
`../line-editing/references/language-conventions.md`. When `story prose`
or `story voices` reports a check skipped for the book's language, do that
pass by reading (see `references/prose-checks.md`, Other languages).

## When to Use

- Starting a project, once the first chapter or a writing sample exists
- Before drafting when voice has drifted between chapters or sessions
- When a copyedit pass needs a style decision recorded (the copyedit itself belongs to the `line-editing` skill, which reads this file)
- When the user wants a mechanical prose check before sharing a draft
- Recording each character's voice (the style sheet's Character Voices line, `voice-words`, `voice-avoid`) and checking it with `story voices`
- NOT for character personality or arc (use `character-management`)
- NOT for scene-level craft such as deep POV or subtext (use `scene-craft`)
- NOT for the line-by-line prose pass itself (line edit, copyedit, read-aloud, proof): use the `line-editing` skill, which reads this style sheet and runs these checks
- NOT for rewriting dialogue so the voices sound distinct when everyone sounds the same: use the `line-editing` skill's voice differentiation pass, which follows the voices recorded here

## Workflow

### 1. Build or update the style sheet

1. Read `story.md` (genre, POV, tense, Tone & Style), `style-sheet.md`,
   and two or three drafted chapters or a sample the user supplies. If
   there is no prose yet, ask the user for a paragraph that sounds right or
   three published books whose voice is close.
2. Fill the sections in `style-sheet.md` following
   `references/style-sheet-guide.md`. Record decisions the prose already
   makes; do not invent new ones silently. When the draft is inconsistent
   (both *grey* and *gray*), ask the user which form wins.
3. Set the frontmatter:
   - `dialect: british | american | unspecified` (`unspecified` for a
     book not in English)
   - one `preferred` entry per variant: `use` is the house form, `avoid`
     the form to flag. Repeat entries for several variants of one word.
   - `watch-words`: words or phrases this book overuses
   - `allow-words`: built-in filter words, adverbs, or dialect spellings
     this book uses on purpose (a proper noun like *Harbor Street* in a
     British book)
   - `samples`: files or folders of the author's own prose that sound right,
     relative to the project folder: an earlier book (`../book-one`) or
     chapters the author has approved, each file named on its own
     (`chapters/chapter-01.md`, never `chapters/`, which warns
     `style-sample-own-chapters`). A listed chapter is the measure, so
     `story prose` does not compare it. Ask the user which; never list prose
     the agent drafted and the author has not approved, or the profile
     measures the agent's voice. With at least 2,000 words of narration,
     `story prose` compares each chapter with the samples instead of fixed
     limits
4. Character Voices entries summarise each character file's Voice & Speech
   Patterns section in one line and link to it. Record words a speaker
   reaches for in the character file's `voice-words` list and words they
   would never say in `voice-avoid`, so `story voices` can check them. The character file is
   canon; if the two disagree, fix the style sheet, or ask the user before
   changing the character.

### 2. Draft and revise against it

- `chapter-writing` and `discovery-drafting` read `style-sheet.md` before
  drafting. Write in the recorded voice, use the house spellings, and give
  each speaker the recorded patterns.
- When a new convention appears mid-draft (a new invented term, a number
  style), add it to the style sheet in the same change.

### 3. Run the prose check

```shell
story prose .
```

The report lists, per chapter: sentence count, average and longest length,
and spread; filter words and -ly adverbs per 1,000 narration words
(dialogue is excluded); plain and said-bookism dialogue tags; words echoed
within 30 words; watch-word counts; and avoided spellings. Across the
manuscript it lists repeated 4-word phrases and character first names that
readers could confuse. Warnings are advisory. The command exits 0 unless a
file cannot be read, a `story.md` `severity` entry promotes a warning to an
error, or the command line is wrong, such as `--baseline` with no `samples`
(exit 2). See `references/prose-checks.md` for what each count means and how
to respond.

When the style sheet lists `samples`, the report opens with a profile of
the author's own prose, and chapters that drift from it warn
(`prose-baseline-sentences`, `-paragraphs`, `-dialogue`, `-filter-words`,
`-adverbs`) in place of the fixed filter-word and adverb limits. Treat a
drift as a prompt to reread the chapter, not a rule. Tell the user where
it drifts and ask whether it is deliberate: a fight scene runs short, a
quiet chapter long. Never rewrite a chapter just to move a number back
inside its tolerance.

To lint a passage that is not in a chapter file yet (a draft scene, a
proposed rewrite), pipe it in with `-` in place of the path:
`story prose - < draft-scene.md`. Run it from the project folder, or add
`--path <project>`, so the style sheet applies. `story voices -` does the
same for dialogue.

### 4. Run the dialogue voice check

```shell
story voices .
```

`story voices` fingerprints each character's attributed dialogue and
warns about a `voice-avoid` word said, a `voice-words` entry never said,
and two characters who may sound alike. A line counts only when the
narration names its speaker by a speech verb, or names one character in
the paragraph. Pronoun tags (`she said`) are never attributed, so in
close third person the POV character is often under-counted; when that
matters, name the tags in a sample chapter and rerun.
`story voices --help` describes the command and, when `story-maintenance`
is installed, the voices section of
[`../story-maintenance/references/continuity-checks.md`](../story-maintenance/references/continuity-checks.md#voices)
gives the full attribution rules and thresholds.

When two voices blur, differentiate them on more than one axis (sentence
length, contractions, vocabulary, what they ask about) and see
`dialogue-subtext.md` in the `scene-craft` skill for the tag-swap test.

Attribution and contraction rates are built around English quote marks,
speech verbs, and contractions. For a book in another language, if the
report attributes few or none of the lines the book has, or skips the
check for the language, compare the voices by reading: the levers
are the same (sentence length, vocabulary, forms of address, what each
avoids saying).

### 5. Act on the findings

1. Fix avoided spellings everywhere; they are always errors of consistency.
2. Treat rates, echoes, and repeated phrases as prompts to reread the
   passage, not orders. Keep a flagged word when it is the right word, and
   add it to `allow-words` when the book uses it deliberately.
3. For uniform-rhythm warnings, revise sentence length by intent (short for
   impact, long for flow), not by formula.
4. For similar names, ask the user before renaming; check replacements with
   `story names '<Candidate>'`. Preview the rename with
   `story rename character <id> '<New Name>' --prose --dry-run`, show the
   user the replacements, then run it without `--dry-run`, so the chapter
   text follows as well as the references. Without `--prose` the prose
   keeps the old name. Check the matches it leaves as written as the
   `character-management` skill's rename steps describe.
5. For `story voices` warnings, revise the dialogue or update the
   character's `voice-words`/`voice-avoid` when the draft has found a
   better voice; ask the user before changing canon.
6. Present a summary: what changed, what was kept on purpose, and any
   style-sheet updates. For a full line edit, copyedit, or proof, hand off
   to the `line-editing` skill.

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
available, apply the checks in `references/prose-checks.md` by reading.

After editing the style sheet or revising prose:

```shell
story reindex .
story wordcount . --write
story check .
story prose .
story voices .
```

## Reference Files

- **`references/style-sheet-guide.md`** - What goes in each style-sheet section, the frontmatter format, and how to extract a voice description from sample prose
- **`references/prose-checks.md`** - What each `story prose` count measures, its threshold, when to keep the flagged text, and what to do for a book not in English
- **`../line-editing/references/language-conventions.md`** - Dialogue and punctuation conventions by language, for the style sheet's Dialogue And Punctuation section

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
