<div align="center">

<h1><img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/banner.svg" alt="Story Skills" width="508"></h1>

**Agent Skills for planning, tracking, and drafting fiction in markdown.**

Story Skills gives agents a shared project format for fiction: a story bible, characters, worldbuilding, factions, artifacts, plot arcs, scenes, continuity state, promises and payoffs, timelines, and chapter drafts. Everything is plain markdown with YAML frontmatter, packaged as standard Agent Skills with Codex and Claude Code plugins. A book can be written in any language: set `language` in `story.md` and the skills draft and edit in it, while the CLI counts, checks, and typesets for it ([Writing in other languages](docs/languages.md)).

The companion `story` CLI treats the story bible as a checkable contract. Its **continuity engine** catches dead characters walking, payoffs that land before their setup, unfired Chekhov guns, and stale story state, deterministically, before a reader finds them.

<img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/demo.gif" alt="story continuity flags a character who died in chapter 2 but appears in chapter 4, a payoff that lands before its setup, and a question resolved before it is asked" width="900">

Why it works this way: [*Story Skills: a continuity compiler for AI-written fiction*](https://ddewhurst.com/blog/story-skills-continuity-compiler-for-ai-fiction/)

[![npm](https://img.shields.io/npm/v/story-skills)](https://www.npmjs.com/package/story-skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/danjdewhurst/story-skills/badge)](https://scorecard.dev/viewer/?uri=github.com/danjdewhurst/story-skills)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-SKILL.md-blue)](https://agentskills.io)
[![Codex](https://img.shields.io/badge/Codex-plugin-10A37F)](https://developers.openai.com/codex)
[![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

</div>

---

## Quick start

**Writing in claude.ai, with no terminal?** [Writers: start here](docs/writers-start-here.md) shows how to download a skill as a zip and upload it to Claude, with nothing to install.

Install the plugin in **Codex** or **Claude Code**:

```shell
# Codex
codex plugin marketplace add danjdewhurst/story-skills
codex plugin add story-skills@story-skills

# Claude Code (type these inside a Claude Code session, not a shell)
/plugin marketplace add danjdewhurst/story-skills
/plugin install story-skills@story-skills
```

For any other agent that supports `SKILL.md`, use the Agent Skills CLI:

```shell
npx skills add danjdewhurst/story-skills   # or: bunx skills add danjdewhurst/story-skills
```

Then ask your agent to **"Start a new story"**. Per-agent instructions for GitHub Copilot, Cursor, Windsurf, Gemini CLI, OpenCode, and others are under [More install options](#more-install-options).

New to Story Skills? [Getting started](docs/getting-started.md) walks through a first session, and the [documentation index](docs/README.md) links every guide and reference page.

### Or let your agent install it

Paste this prompt into your coding agent. It works out which agent it is and uses the matching install method:

```text
Install the Story Skills bundle from https://github.com/danjdewhurst/story-skills.

First, work out which agent you are, then use the matching method below. If a command fails or you can't run it, tell me the exact command to run myself.

- Claude Code: run `claude plugin marketplace add danjdewhurst/story-skills`, then `claude plugin install story-skills@story-skills`. If the `claude` CLI isn't available, tell me to type `/plugin marketplace add danjdewhurst/story-skills` and then `/plugin install story-skills@story-skills` in this session.
- Codex: run `codex plugin marketplace add danjdewhurst/story-skills`, then `codex plugin add story-skills@story-skills`.
- Gemini CLI: run `gemini skills install https://github.com/danjdewhurst/story-skills.git`.
- Any other agent that supports SKILL.md (GitHub Copilot, Cursor, Windsurf, OpenCode, and others): run `npx skills add danjdewhurst/story-skills`, or `bunx skills add danjdewhurst/story-skills` if only Bun is installed. If that doesn't support you, clone the repository to a temporary directory and copy every folder in its `skills/` directory into your skills directory:
  - GitHub Copilot: `.github/skills/` in this project, or `~/.copilot/skills/` globally
  - Cursor: `.agents/skills/` in this project
  - Windsurf: `.windsurf/skills/` in this project, or `~/.codeium/windsurf/skills/` globally
  - OpenCode: `.opencode/skills/` in this project, or `~/.config/opencode/skills/` globally
  - Anything else: your documented skills directory, or `.agents/skills/` in this project

Prefer a project install unless I asked for a global one. If you can't tell which agent you are, ask me before installing. When you're done, tell me what you installed, where it went, and whether I need to restart or reload you for the skills to show up.
```

## The continuity engine

Long-range consistency is what language models are worst at, and prompting can't fix it. Story Skills makes it deterministic: character deaths, promises and payoffs, open questions, scene casts, and durable knowledge and object state live in frontmatter, and `story continuity` treats contradictions the way a compiler treats type errors.

[`examples/the-unraveled-thread/`](examples/the-unraveled-thread/) is a deliberately broken mystery. Every file is well-formed, so it passes `story validate` and `story links` cleanly, but the story itself doesn't hold together:

<!-- replay exit=1 -->
```text
$ story continuity examples/the-unraveled-thread
Continuity check failed: 4 errors, 3 warnings, 0 dismissed
error: chapters/chapter-04.md lists edran-vale, who died in chapter-02; move posthumous appearances to mentions
error: continuity/promises/the-broken-compass.md pays off in chapter-02 before it is planted in chapter-03
error: continuity/questions/who-burned-the-mill.md resolves in chapter-02 before it is introduced in chapter-03
error: continuity/state.md knowledge-state[0] references missing chapter chapter-05
warning: chapters/chapter-03.md POV character nessa-thorn is not listed in characters [pov-not-in-cast]
warning: continuity/promises/the-sealed-letter.md was planted in chapter-01, 3 chapters ago, and has no payoff yet [promise-unpaid]
warning: continuity/state.md object-state[0] status active conflicts with worldbuilding/artifacts/vales-compass.md status destroyed [state-status-conflict]
```

Every finding is exact, file-addressed, and reproducible, and CI asserts this output on every commit. Intentional flashbacks and posthumous appearances stay legal through the chapter `mentions` field, and findings listed in `continuity/exemptions.md` are reported as dismissed. `story doctor` and `story next` fold the same checks into prioritized repair actions.

## Skills

| Skill | What it does | Try saying |
|-------|-------------|------------|
| **premise-workshop** | Turns a spark into a tested premise: what-ifs, logline tests, premise and counter-premise, stakes, choice of form, titles, and comparable books, then hands off to `story init --form` | *"Is there a novel in this idea?"* |
| **story-init** | Scaffolds the story bible, folders, and registries | *"Start a new story"* |
| **character-management** | Creates character profiles with relationships, traits, arcs, and family trees | *"Create a character"* |
| **worldbuilding** | Builds locations and systems (magic, politics, technology, religion, and more) and the glossary of invented terms | *"Design a magic system"* |
| **plot-structure** | Plans arcs with structures like three-act, hero's journey, Save the Cat, and kishotenketsu | *"Create a plot arc"* |
| **theme-craft** | Builds the controlling idea (value + cause premise), the moral argument, lie/truth arc types, antagonist design, and motif/symbolism audits | *"What's my story really about?"* |
| **genre-craft** | Genre packs with checkable conventions: mystery fair-play, romance beats, thriller, horror, MG/YA, sci-fi, fantasy, historical, comedy, and serial/episodic structure | *"Plan a fair-play mystery"* |
| **research** | Investigates the real-world facts a story relies on, with quoted sources, confidence, interviews and site visits, invented-versus-accurate decisions, and qualified reviewers for legal, medical, and other risky details | *"Fact-check the sailing in chapter 4"* |
| **chapter-writing** | Drafts chapters through an outline-first workflow that pulls from story context | *"Write the next chapter"* |
| **discovery-drafting** | Pantsing mode: draft from a story kernel, keep post-hoc chapter notes, and reconcile the bible after each discovery-drafted chapter | *"I want to discovery-write"* |
| **scene-craft** | Plans and checks the scene unit: Scene/Sequel structure, try/fail cycles, scene cards, dialogue subtext and voice differentiation, deep POV, exposition, flashbacks, and openings | *"Does this chapter breathe?"* |
| **voice-style** | Keeps a copyeditor's style sheet (dialect, house spellings, dialogue punctuation, character voices, watch words) and acts on `story prose` lint findings | *"Set up a style sheet for this book"* |
| **verse-craft** | Writes, scans, and fixes verse: limericks, sonnets, haiku, ballads, song lyrics, rhyming picture-book text, and a character's song or prophecy, with every line's stresses and the rhyme scheme shown so the author can check them | *"Does this limerick scan?"* |
| **interactive-fiction** | Plans, drafts, and revises branching and choose-your-own-adventure books: the choice graph, chapter `choices`, prose that holds on every path to a rejoin, endings, path continuity, and Twine and ink builds | *"Plan where the branches rejoin"* |
| **line-editing** | Owns the prose pass without flattening the author's voice: line edits with a reason for each change, distinct character voices checked by `story voices`, a copyedit against the style sheet, and read-aloud and proof passes | *"Line edit chapter 3. Everyone sounds the same."* |
| **revision-continuity** | Revises drafts, audits continuity, and keeps character state, timeline, and arc changes consistent | *"Continuity-check chapter 3"* |
| **reader-panel** | Runs simulated persona reads of a chapter range (genre reader, line editor, sensitivity flags, continuity reader, first-page reader) before human readers see it, written as feedback files marked `source: simulated` for feedback-triage | *"Give me a simulated beta read of chapters 1 to 5"* |
| **feedback-triage** | Sends readers a review copy (optionally on GitHub Pages with a note form), collects alpha/beta reader feedback per round, synthesizes convergent and divergent notes, and hands a revision plan to revision-continuity | *"Triage the beta feedback"* |
| **editorial-review** | Handles work with other people: sensitivity and authenticity reader briefs, a real-people and defamation check, permissions for lyrics and epigraphs, the AI-use statement, rounds with human editors and their review copies, and co-authoring | *"I'm quoting a song lyric as my epigraph. What do I need?"* |
| **series-continuity** | Starts sequels and prequels as linked projects, carries characters and world forward, checks shared canon across books, and pitches a series | *"Start a prequel to The Last Ember"* |
| **submission** | Checks submission readiness, drafts the query letter, pitch, comp titles, synopsis, and blurb, builds the Shunn manuscript, and tracks queries and responses | *"Help me query agents"* |
| **publishing** | Self-publishing production: retailer metadata, ISBNs, the copyright page, accessible EPUB and print interiors, distribution, pricing, a launch plan with ARCs and ad testing, and a rights inventory with contract red flags | *"Get my book ready for KDP and IngramSpark in 6x9"* |
| **adaptation** | Carries the story into other forms: an audiobook narration script with a pronunciation guide, a Fountain screenplay, a picture-book spread plan with illustration briefs, a comics script, an interactive edition of a linear book, and translated editions | *"Make a narration script so I can audition narrators"* |
| **story-maintenance** | Runs deterministic CLI checks for validation, continuity, reports, indexing, links, word counts, import, and export | *"Validate my story project"* |

**line-editing** owns the prose pass. For general-purpose writing checks as well, add [**better-writing**](https://github.com/forjd/better-writing). It adds voice calibration, anti-generic writing checks, and a final prose-quality pass, and installs the same way:

```shell
npx skills add forjd/better-writing
```

## Companion CLI

The optional `story` CLI handles deterministic project maintenance while the skills handle the creative work. It needs Node 18 or newer and has no runtime dependencies. Run it with `npx`, or install it globally:

```shell
npx story-skills --help
npm install -g story-skills   # then: story --help (Windows too)
```

To try unreleased changes, run it straight from GitHub with `npx --yes --package github:danjdewhurst/story-skills story --help`.

**Without Node.** Releases after 0.17.0 attach a standalone `story` binary for macOS (Apple silicon and Intel), Linux (x64 and arm64), and Windows (x64). Install it with Homebrew on macOS or Linux, or, on any system including Windows, download the archive for your system from the [releases page](https://github.com/danjdewhurst/story-skills/releases), check it against the release's `story-skills_<version>_checksums.txt`, and put `story` on your `PATH` ([details](docs/getting-started.md#install-the-story-cli)):

```shell
brew install danjdewhurst/tap/story-skills   # then: story --help
```

The binary is the CLI only, and reports the same `story --version` as the npm package. The skills still need an agent such as Claude Code or Codex (see [Quick start](#quick-start)).

From a clone, run `node <clone>/bin/story.js <command>` (or `bun <clone>/bin/story.js <command>`) from your project folder, or for `init` and `import` from the folder that should hold the new project. Bun reads `bunfig.toml` and `.env` from the current folder, so use it only in projects you trust. Copied-skill installs don't need a clone: `story-maintenance` bundles a `scripts/story.js` fallback that agents run with Node.

The CLI is for maintenance only. Agents write story content directly to markdown files and never create project-local build or generator scripts to emit the story.

**Create and restructure**

| Command | Purpose |
|---------|---------|
| `story init "The Last Ember"` | Scaffold a story project with the standard markdown layout |
| `story init "Book Two" --follows the-last-ember` | Scaffold a sequel (or a prequel with `--precedes`) linked to an existing book, writing the backlink |
| `story import draft.md --title "The Lost Coast"` | Split an existing manuscript into a new story project and suggest entity candidates; `--language` reads Spanish, French, or German chapter headings |
| `story add character "Sera Voss"` | Create entity files for characters, locations, systems, factions, artifacts, arcs, chapters, scenes, questions, promises, clues, terms, research notes, and matter pages |
| `story add matter "Dedication"` | Add a front (default) or `--placement back` matter page such as a dedication, epigraph, or acknowledgments |
| `story add character "李明" --id li-ming` | Give the id by hand for a name the CLI cannot slug (Cyrillic and Greek names are transliterated), so the name keeps its own script |
| `story names "Seren" "Kestrel Row"` | Check candidate names against every name, alias, and glossary term before using them: clashes fail, look-alikes warn |
| `story mentions character sera-voss` | List every place chapter prose names an entity (name, given name, or alias), and which chapters name it without listing it; with no entity, check every chapter's names against its frontmatter |
| `story rename character sera-voss "Sera Vale"` | Rename an entity and update kebab-case references |
| `story move chapter chapter-03 --number 4` | Renumber a chapter, or move a scene with `story move scene <id> --chapter <id>`, renaming the files and rewriting every reference to the old id |
| `story split chapter-03 --at 2` | Split a chapter in two at a scene break, heading, or line, or join two with `story merge chapter-03 chapter-04`, renumbering the chapters after them and updating references |
| `story remove promise old-setup` | Remove an entity and scrub metadata references |
| `story migrate [path]` | Upgrade a project to the current schema |

**Check and repair**

| Command | Purpose |
|---------|---------|
| `story validate [path]` | Check required files, schema version, YAML frontmatter, registries, and word-count warnings |
| `story links [path]` | Check character, location, chapter, and arc cross-references and backlinks |
| `story continuity [path]` | Check deterministic continuity contracts: deaths, promises and payoffs, questions, casts, durable state, and travel times along location routes |
| `story check [path] --strict` | Run validate, links, and continuity in one scan, listing each finding once; `--strict` fails on warnings too |
| `story list chapters --where status=draft` | List the chapters, scenes, characters, or other entities whose frontmatter matches every `--where` filter (`key=value`, which also matches inside a list, `key!=value`, `key`, or `!key`), in book order; `--query <name>` runs a filter set saved in `story.md` `queries`; `--json` for scripts |
| `story series [path]` | Order linked sequels and prequels by chronology and check shared canon: deaths, casts, knowledge fact ids, names, and destroyed artifacts |
| `story reindex [path]` | Rebuild registry tables from the current markdown files |
| `story wordcount [path] --write` | Count chapter prose and update chapter frontmatter plus the chapter registry; Chinese and Japanese books count characters (`count-unit`) |
| `story doctor [path]` | Show health checks with actionable repair steps |
| `story next [path]` | Recommend the next deterministic writing or maintenance actions, including the next revision pass while revising |
| `story passes [path] --init` | Record named revision passes (structure, character, theme, continuity, pacing, line, copyedit, proof) in `story.md`; `--start` and `--done` mark progress |
| `story report [path] --actionable` | Summarize inventory and optionally include next actions |

**Analyze**

| Command | Purpose |
|---------|---------|
| `story knowledge sera-voss --at chapter-03` | Show what a character knew at a chapter, marked reader-knowledge or character-knowledge |
| `story context chapter-03 --budget 6000` | Pack the drafting context for a chapter or scene into a token budget. Later chapters are left out; an unread flashback fact is marked character-knowledge, do not reveal |
| `story timeline [path]` | Show scenes in story-time order from their `date`/`time` (marking scenes told out of order), POV balance by words, and each character's presence and longest absence |
| `story prose [path]` | Lint chapter prose: filter words, adverbs, said-bookisms, echoes, sentence rhythm, repeated phrases, similar names, and `style-sheet.md` spellings and watch words. Word lists follow the book's `language` (English, Spanish, French, and German built in); a check with no list for the language is skipped with a note |
| `story voices [path]` | Fingerprint each character's attributed dialogue (sentence length, contractions, questions, signature words) and flag `voice-avoid` words and characters who sound alike. Only named speech tags and single-name action beats count; pronoun tags do not |
| `story pacing [path]` | Tabulate scenes, sequels, scene outcomes (`yes`, `no`, `yes-but`, `no-and`), and chapter hooks; flag runs of easy wins, missing sequels, flat chapter endings, and length outliers |
| `story clues [path]` | Draw the fair-play grid of clue plants and reveals by chapter; flag late plants, unplanted reveals, and red herrings never debunked |
| `story grid [path]` | Print the plot grid of arcs by chapter from `arcs-advanced`, with each chapter's beat, hook, and scene outcomes, as a markdown table or `--format csv`; `--from` and `--to` show a range of chapters |
| `story diagram relationships --path .` | Print Mermaid source for the family tree and relationships, the location route map, the story-time timeline, the clue flow, or arcs by chapter |
| `story progress [path] --log` | Report words against `target-words` (or characters against `target-characters`), the `deadline`, and chapter targets; `--log` records the day's count in `progress.md` for pace, a projected finish, today's words against `daily-target-words`, a writing streak, and weekly totals |
| `story snapshot draft-1` | Save a named copy of the project's markdown in `.snapshots/`, which every command skips, to compare with later; no git needed. `--list` shows the snapshots, and `--restore draft-1` puts one back after saving the project as it is |
| `story compare [path] --ref draft-1` | Compare chapters with an earlier draft (a git ref, `--snapshot` a saved snapshot, or `--against` a copied project folder): word changes, added and removed chapters, and unchanged paragraphs; `--anchor ch03-p12` finds where a review-copy paragraph is now |
| `story similarity [path] --against ../book-one` | Find passages that share a run of eight or more words with other text (a file, a folder such as your earlier books, a git ref, or `--snapshot` a saved snapshot), with both locations and the shared words; advisory, since shared text is not proof of copying |

**Publish**

| Command | Purpose |
|---------|---------|
| `story synopsis [--pages 1\|3] [--out file]` | Compress arcs into a mechanical 1- or 3-page synopsis |
| `story export [path] --out dist/manuscript.md` | Combine front matter, chapters, and back matter into a single manuscript markdown file |
| `story build [path] --format epub` | Build disposable markdown, EPUB, DOCX, or Shunn manuscript artifacts in `dist/`; EPUB builds embed the `story.md` `cover` image, publishing metadata, and accessibility metadata |
| `story build [path] --format html` | Build a single-file review copy whose paragraphs carry citable anchors such as `ch03-p12` |
| `story build [path] --format print --trim 6x9` | Build a print-ready paged-media HTML interior (author and chapter-title running heads, foot page numbers, raised chapter initials) to render to PDF with Paged.js, WeasyPrint, or Prince; add `--pdf` to run an installed engine and write the PDF |
| `story build [path] --format narration` | Build an audiobook narration script with a pronunciation guide and runtime estimates |
| `story build [path] --format codex` | Build the story bible as a static, cross-linked HTML site in `dist/codex/` (spoiler-safe unless `--spoilers`) |
| `story build [path] --format metadata` | Build a retailer metadata sheet from `story.md` with a readiness checklist |
| `story build [path] --format fountain` | Build a Fountain screenplay skeleton, one scene heading per scene record, to draft an adaptation into |
| `story build [path] --format twee` | Build a branching book, whose chapters link through `choices`, as a Twine story in Twee 3; `--format ink` builds it as an ink story for Inky and inklecate |

Behavior notes:

- **Matter pages** from `matter/` appear in the export and in every build format except Shunn, which is a submission format.
- **EPUB and DOCX** builds target plain prose: `*italic*` and `**bold**` become italic and bold runs, scene-break lines (`***`, `---`) become a `* * *` separator, and other markdown structure such as blockquotes, lists, and tables is flattened to text. The markdown export keeps chapter text as-is.
- **Books not in English** get build text in their language (chapter headings, contents, copyright page, EPUB accessibility text) in 18 languages, overridable with `labels` in `story.md`. Builds set Arabic, Hebrew, Persian, and other right-to-left languages right to left, pick fonts for the script, can set Japanese, Chinese, and Korean vertically (`writing-mode: vertical`), and can print native chapter numerals (`chapter-numerals: native`, such as `第十二章`). See [Writing in other languages](docs/languages.md).
- **`story rename`, `story move`, and `story remove`** update entity ids in frontmatter reference fields and markdown link targets. They never edit prose, except `story rename --prose`, which replaces the name in chapter text as written and as whole words, so a character called "Port" can be renamed without touching the word "port".
- A command that changes a frontmatter value rewrites only the entries that changed. Comment lines, unchanged entries, and the body keep their exact text, and files whose values don't change are left untouched.

Every command and option is in the [CLI reference](docs/cli-reference.md). For a complete first session, read [Getting started](docs/getting-started.md). For the project contract, read the [Project format reference](docs/project-format.md) and [`schemas/story.schema.json`](schemas/story.schema.json).

## Write a book with pull requests

A story project with deterministic checks is one an agent can advance unattended. The [`templates/github/`](templates/github/) workflows turn a story repository into a self-drafting book:

- [`story-checks.yml`](templates/github/story-checks.yml) runs `story check` (validate, links, and continuity in one scan) and `story report --actionable` on every push and pull request, so a chapter PR can't merge with a continuity contradiction.
- [`draft-next-chapter.yml`](templates/github/draft-next-chapter.yml) runs [Claude Code](https://github.com/anthropics/claude-code-action) on a schedule. It asks `story next` for the next action, drafts the next chapter with the chapter-writing skill, updates scene records and continuity state, and commits it within word, turn, and spend budgets. The agent cannot push. A second job, on a fresh runner, checks that the commit touches only the story's own markdown and holds no secret, runs the checks, pushes the branch, and opens a pull request for review: ready when the checks pass, a draft listing the failures when they do not. When `story next` suggests no chapter (the story is revising or complete, or every arc is resolved), it stops without drafting.

Copy both files into `.github/workflows/` in the repository that holds your story project, add an `ANTHROPIC_API_KEY` secret, and review one chapter PR each morning.

GitHub doesn't start `story-checks.yml` for pull requests opened with the built-in `GITHUB_TOKEN`, so the draft workflow runs the same checks itself after drafting. Pass a personal access token as `github_token` if you also want the checks workflow to run on those PRs.

Readers who never open a terminal can review the book too:

- [`review-copy.yml`](templates/github/review-copy.yml) builds `story build --format html` on every push to `main` and publishes it to GitHub Pages. Every paragraph in the review copy carries a label such as `ch03-p12`, so a note can point at an exact place.
- [`ISSUE_TEMPLATE/manuscript-note.yml`](templates/github/ISSUE_TEMPLATE/manuscript-note.yml) is an issue form that asks readers for that label, the kind of note, and how much it affected their reading. The feedback-triage skill turns those issues into a feedback round.

Copy the workflow into `.github/workflows/` and the form into `.github/ISSUE_TEMPLATE/`, then set **Settings > Pages > Source** to GitHub Actions. Pages sites are public unless your plan supports private Pages; for a private manuscript, delete the deploy job and share the workflow artifact instead.

## Import an existing manuscript

Most writers don't start from a blank page. `story import` builds a Story Skills project from work in progress:

```shell
story import draft.md --title "The Lost Coast" --genre mystery
story import brouillon.md --title "La Côte perdue" --language fr
```

It splits the manuscript on chapter headings (or imports a directory of chapter files in natural name order, so `chapter-2` comes before `chapter-10`), creates the full project layout with accurate word counts and registries, and prints recurring proper-name candidates so an agent can follow up with `story add character` and `story add location` to build out the bible.

`--language` sets the manuscript's language, writes it to the new `story.md`, and splits on that language's own chapter headings: `Chapter` in English (the default), `Capítulo` in Spanish, `Chapitre` in French, and `Kapitel` in German. For a manuscript in any other language, import a folder with one file per chapter.

`--force` lets an import reuse an existing directory. It replaces every `chapter-NN.md` file in `chapters/`, so stale chapters from an earlier import are removed. It saves the project as snapshot `before-import-<n>` first, and `story snapshot --restore before-import-<n>` puts the old chapters back.

## Project structure

Running **story-init** creates this layout:

```
my-story/
├── story.md                  # Story bible: title, genre, themes, POV, tense
├── style-sheet.md            # Voice, house spellings, and watch words
├── characters/
│   └── _index.md             # Character registry
├── worldbuilding/
│   ├── _index.md             # World overview
│   ├── locations/
│   ├── systems/
│   ├── factions/
│   └── artifacts/
├── plot/
│   ├── _index.md             # Arc overview
│   ├── arcs/
│   └── timeline.md
├── scenes/
│   └── _index.md             # Machine-readable scene registry
├── continuity/
│   ├── state.md              # Character, object, and knowledge state
│   ├── questions/
│   │   └── _index.md
│   ├── promises/
│   │   └── _index.md
│   └── clues/
│       └── _index.md
├── glossary/
│   ├── _index.md
│   └── terms/
└── chapters/
    └── _index.md             # Chapter registry
```

Some files appear only once you need them: `matter/` for front and back matter, `research/` for research notes, `progress.md` for the session log written by `story progress --log`, and `continuity/exemptions.md` for dismissed continuity findings.

## How it works

Every story element is a markdown file with YAML frontmatter, and the skills cross-reference those files to keep the project consistent:

- **`story.md`** is the top-level bible that every skill reads. Its **`schema-version: 2`** field lets the CLI detect incompatible project formats.
- Every entity file is named by a **kebab-case identifier**, such as `sera-voss` or `chapter-01`. It comes from the entity's name, or from `story add --id` when the name has nothing to slug; Cyrillic and Greek names are transliterated (`Пётр` gives `petr`), and names themselves may be written in any script.
- **`_index.md`** files are the registries for each domain.
- Relationships and references are kept **bidirectional**.
- Scene records and continuity state keep character knowledge, object ownership, and setups and payoffs in files, so they carry over between sessions.

## Examples

Complete projects generated with Story Skills:

- [**The Cormorant Tide**](https://github.com/danjdewhurst/the-cormorant-tide)
- [**Pippa and the Borrowed Star**](https://github.com/danjdewhurst/christmas-childrens-story), a children's Christmas story (6 chapters, 2,183 words)

Examples in this repository:

- [`examples/the-last-ember/`](examples/the-last-ember/): a fantasy with three characters, two locations, a magic system, a plot arc with foreshadowing, and a drafted first chapter.
- [`examples/the-fall-of-the-citadel/`](examples/the-fall-of-the-citadel/): a prequel to The Last Ember, linked with `series`, `book-number`, and `precedes`, that shares characters and places with the first book. Run `story series examples/the-last-ember` to see the chronology.
- [`examples/harbor-of-second-light/`](examples/harbor-of-second-light/): a near-future coastal mystery with memory technology, a posthumous witness arc, populated continuity state, and a drafted first chapter.
- [`examples/the-gull-rock-light/`](examples/the-gull-rock-light/): a short branching story whose chapters carry `choices`; `story build --format twee` turns it into a Twine story and `--format ink` into an ink story.
- [`examples/bo-and-the-missing-moon/`](examples/bo-and-the-missing-moon/): a 32-page picture book (`form: picture-book`), one chapter per spread, each with a scene record and a page-turn `hook`, and a pagination plan with spread briefs in `adaptations/picture-book/`.
- [`examples/the-left-luggage-office/`](examples/the-left-luggage-office/): the first three episodes of a weekly serial (`form: serial`), with a `season-goal`, an `episode-question`, `target-words`, and a cliffhanger `hook` on each episode, and a promise scheduled for an episode not yet written.
- [`examples/salt-and-lantern/`](examples/salt-and-lantern/): an anthology of three short stories by different writers, with the editor credited by `editor` in `story.md`, each story's writer by its chapter `author`, title-only story headings, and an acknowledgements page.
- [`examples/the-unraveled-thread/`](examples/the-unraveled-thread/): a deliberately broken project that demonstrates the main kinds of finding the continuity engine reports.
- [`examples/quatre-heures-dix-sept/`](examples/quatre-heures-dix-sept/): a short story in French (`language: fr`), with dialogue in guillemets and French no-break spaces, checked by the French word lists, and built with French chapter headings and labels.
- [`examples/kirimi-eki-no-wasuremono/`](examples/kirimi-eki-no-wasuremono/): a short story in Japanese (`language: ja`), counted in characters and set in vertical columns (`writing-mode: vertical`), with dialogue in corner brackets.
- [`examples/laysat-lil-bay/`](examples/laysat-lil-bay/): a short story in Arabic (`language: ar`), built right to left, with Arabic punctuation.

[Writing in other languages](docs/languages.md) covers what works in each language and script.

## More install options

<details>
<summary><strong>Codex (without the plugin)</strong></summary>

The plugin install in [Quick start](#quick-start) is the recommended path. For local skill authoring, copy the skills in directly; Codex detects repo and user skills automatically:

```shell
git clone https://github.com/danjdewhurst/story-skills.git

# User-wide
mkdir -p ~/.agents/skills && cp -r story-skills/skills/* ~/.agents/skills/

# Or repo-scoped
mkdir -p .agents/skills && cp -r story-skills/skills/* .agents/skills/
```

</details>

<details>
<summary><strong>GitHub Copilot (VS Code)</strong></summary>

[VS Code with Copilot](https://code.visualstudio.com/docs/copilot/customization/agent-skills) discovers skills from several directories:

```shell
git clone https://github.com/danjdewhurst/story-skills.git

# Copy skills to your project (either works)
mkdir -p .github/skills && cp -r story-skills/skills/* .github/skills/
mkdir -p .agents/skills && cp -r story-skills/skills/* .agents/skills/

# Or install globally
mkdir -p ~/.copilot/skills && cp -r story-skills/skills/* ~/.copilot/skills/
```

Copilot can activate a skill when your request matches its description, or you can invoke one manually.

</details>

<details>
<summary><strong>Cursor</strong></summary>

[Cursor](https://www.cursor.com) supports the `SKILL.md` standard:

```shell
git clone https://github.com/danjdewhurst/story-skills.git
mkdir -p .agents/skills && cp -r story-skills/skills/* .agents/skills/
```

</details>

<details>
<summary><strong>Windsurf</strong></summary>

[Windsurf](https://windsurf.com) discovers skills from workspace and global directories:

```shell
git clone https://github.com/danjdewhurst/story-skills.git

# Copy skills to your project
mkdir -p .windsurf/skills && cp -r story-skills/skills/* .windsurf/skills/

# Or install globally
mkdir -p ~/.codeium/windsurf/skills && cp -r story-skills/skills/* ~/.codeium/windsurf/skills/
```

Cascade can invoke a matching skill automatically, or you can use `@skill-name` to invoke one directly.

</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

[Gemini CLI](https://github.com/google-gemini/gemini-cli) supports the same `SKILL.md` format through the [Agent Skills](https://agentskills.io) standard:

```shell
# Install all skills globally
gemini skills install https://github.com/danjdewhurst/story-skills.git

# Or install a single skill (any folder under skills/)
gemini skills install https://github.com/danjdewhurst/story-skills.git --path skills/chapter-writing

# Or link locally after cloning
git clone https://github.com/danjdewhurst/story-skills.git
gemini skills link story-skills/skills
```

Gemini can activate a skill when your request matches its description.

</details>

<details>
<summary><strong>OpenCode</strong></summary>

[OpenCode](https://opencode.ai) supports the `SKILL.md` format natively:

```shell
git clone https://github.com/danjdewhurst/story-skills.git

# Copy skills to your project
mkdir -p .opencode/skills && cp -r story-skills/skills/* .opencode/skills/

# Or install globally
mkdir -p ~/.config/opencode/skills && cp -r story-skills/skills/* ~/.config/opencode/skills/
```

OpenCode also searches common skill paths such as `.claude/skills/`, so it can find project-level skills installed for other agents.

</details>

<details>
<summary><strong>Other platforms</strong></summary>

These skills follow the open [Agent Skills](https://agentskills.io) standard. If your agent supports the Agent Skills CLI, install the bundle directly:

```shell
npx skills add danjdewhurst/story-skills   # or: bunx skills add danjdewhurst/story-skills
```

Use `--skill <name>` to install only specific skills, or `--agent <name>` to target a supported agent. You can also copy the skill folders into any compatible agent's skills directory.

Outside coding agents:

- **Claude.ai or ChatGPT Projects**: add the `SKILL.md` and reference files as project knowledge.
- **Any LLM API**: include the skill content in the system prompt.
- **By hand**: the templates, workflows, and project structure are model-agnostic.

</details>

## Development and releasing

To contribute, start with [CONTRIBUTING.md](https://github.com/danjdewhurst/story-skills/blob/main/CONTRIBUTING.md) and the [Code of Conduct](https://github.com/danjdewhurst/story-skills/blob/main/CODE_OF_CONDUCT.md). User-visible changes are listed in the [changelog](CHANGELOG.md). The [Development guide](docs/development.md) covers the repository layout, CLI architecture, tests, and release process in full. Development uses Bun:

```shell
bun install
bun run test
bun run test:coverage
bun run test:examples   # also validates every example against schemas/story.schema.json
bun run check:metadata
```

`bun run build:fallback` generates the copied-skill fallback CLI from the package entrypoint. After changing CLI source, rebuild it, check it is current, and confirm it runs under Node:

```shell
bun run build:fallback
bun run check:fallback
node skills/story-maintenance/scripts/story.js --help
```

The `evals/` harness regression-tests the writing skills. Fixtures seed a drafting brief with known canon and known traps. A dependency-free checker verifies that drafts keep the canon and spring none of the traps, a model runner (requires the `claude` CLI) drafts through a real model and judges for invented canon, and a pairwise comparison measures the skill against a no-skill baseline. See [`evals/README.md`](https://github.com/danjdewhurst/story-skills/blob/main/evals/README.md).

```shell
bun run check:evals      # validate fixture schemas
bun run eval:selftest    # checker self-test against known-good drafts
node evals/run-skill.js  # full model run (needs Claude Code credentials)
```

Every published change needs a new version in `package.json`, `.codex-plugin/plugin.json` (Codex's version source), `.claude-plugin/plugin.json` (Claude Code's), and `src/version.js` (printed by `story --version`), so installed users receive updates. Marketplace entries stay unversioned to avoid duplicate version state.

Don't bump these by hand. The release script bumps all four, plus the template `STORY_VERSION` pins and the version examples in the docs, moves the `Unreleased` entries in `CHANGELOG.md` under the new version (and refuses to run while there are none), rebuilds the fallback, runs the local preflight checks (a subset of CI), commits `chore: release X.Y.Z`, tags `vX.Y.Z`, pushes, and creates a GitHub release with generated notes. The tag push runs the Publish workflow, which waits for CI to pass on `main` for the release commit, then publishes the package to npm with provenance through trusted publishing. The script requires a clean `main` that matches `origin/main`, a logged-in `gh`, admin rights on the repository (only admins can create `v*` tags), and a version that isn't already on npm:

```shell
bun run release patch            # or minor, major, or an explicit version like 1.2.0
bun run release patch --dry-run  # run the checks and print the plan without changing anything
```

Distribution metadata lives in `.claude-plugin/` for Claude Code and in `.codex-plugin/` plus `.agents/plugins/marketplace.json` for Codex. The `plugins/story-skills` symlink is intentional: Codex marketplace entries must point at a child plugin directory, so the symlink exposes the repo-root plugin without duplicating `skills/`.

## License

[MIT](LICENSE)
