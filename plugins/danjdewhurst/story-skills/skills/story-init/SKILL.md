---
name: story-init
description: This skill should be used when the user asks to "start a new story", "initialize a story project", "create a story", "new book", "set up a story", or wants to begin a new fiction writing project from scratch. NOT for a sequel or prequel (use series-continuity), or for finding the idea before a project exists (use premise-workshop).
---

# Story Initialization

## Overview

Initialize a new story project with a structured markdown folder layout. Creates the story bible, registries, scene tracking, continuity state, glossary, worldbuilding folders, plot structure, and chapter tracker - all as cross-referenced markdown files with YAML frontmatter.

## When to Use

- Starting a new story, book, or fiction project
- Setting up the folder structure for an existing story idea
- NOT for adding to an existing story project (use the domain-specific skills instead)
- NOT for a sequel, prequel, or companion to an existing book: use `series-continuity`, which links the projects and carries canon across
- NOT for finding the idea itself: when the user has only a vague notion ("something about lighthouses"), several competing ideas, or no premise yet, run the `premise-workshop` skill first, then return here with the chosen premise, form, and genre
- NOT for converting an existing manuscript or chapter drafts: run `story import '<source>' --title '{Title}'` instead, then build out the bible from the entity candidates it prints. Import does not accept `--form`, so afterwards set `form` and `target-words` in `story.md` by hand (see the form list and defaults below); without them `story validate` never checks length and `story progress` has no target

## Workflow

1. Ask for basic story information (if a `premise-workshop` session produced a premise, logline, genre, and form, reuse them rather than asking again):
   - Title
   - Form: `novel`, `novella`, `novelette`, `short-story`, `flash`, `serial`, `picture-book`, or `chapter-book`. Without `--form`, `story init` writes no `form` and no `target-words`, so if the user doesn't choose, pass `--form novel`
   - Genre and sub-genre
   - Brief synopsis (2-3 sentences)
   - Setting era/time period
   - Key themes (2-4)
   - POV style (first-person, third-person-limited, third-person-omniscient)
   - Tense (past, present, future, mixed)
   - Language the book is written in, as a BCP 47 tag: `en`, `en-GB`, `fr`, `es-MX`, `pt-BR`, `de`, `ja`, `zh-Hans`. Add a region only when it matters (spelling, punctuation, or market). If the user writes to you in a language other than English, confirm rather than assume. Default `en`

If the Story CLI is available, prefer using it to create the starter project, then inspect and refine the generated files as needed:

```shell
story init '{Title}' --form '{form}' --genre '{genre}' --sub-genre '{sub-genre}' --setting-era '{era}' --pov '{pov-style}' --tense '{tense}' --synopsis '{synopsis}' --theme '{theme-1}' --theme '{theme-2}'
```

The values are the user's own words, so wrap each one in single quotes. Never paste a value into double quotes, where `$(...)`, backticks, and `"` still take effect. A single quote inside a value depends on the shell: write it as `'\''` in a POSIX shell (bash, zsh, sh, Git Bash) and as `''` in PowerShell. Never run the command in cmd.exe, which has no single quotes and runs `&` inside a value; use PowerShell or a POSIX shell.

`--form` records `form` in `story.md` and, when no target is given, sets a default `target-words` for the form (novel 80,000, novella 30,000, novelette 12,000, short story 5,000, flash 1,000, chapter book 10,000, picture book 500; serials get no book-level default). `story validate` then warns when `target-words` is outside the form's usual range. For short forms, point the user to `references/short-story-form.md` in the `plot-structure` skill.

Record the language straight after init. `story init` has no flag for it, so add `language: {tag}` to the `story.md` frontmatter by hand, with the exact tag the user gave, regional variants such as `en-GB` or `en-AU` included. Write it for English books too: it costs nothing, and a missing field only means `en`. The language is not just metadata: drafting, editing, and critique skills write and judge prose in it, `story validate` checks the tag, and builds declare it. For a book not in English, set `dialect: unspecified` in `style-sheet.md` (the British and American spelling pairs are English) and, before the first chapter, settle the dialogue punctuation with the `voice-style` skill.

A Chinese (`zh`) or Japanese (`ja`) book is counted in characters, not words: `story wordcount`, `story progress`, the registries, and the form check all measure characters, against `target-characters`. Because the language is added after init, `--form` will have written a `target-words`; replace it with `target-characters` for the form (Chinese: novel 200,000, novella 60,000, short story 10,000, flash 1,500; Japanese: novel 150,000, novella 80,000, short story 20,000, flash 4,000), or a number the user names. No source sets a novelette, picture-book, or chapter-book length in characters, so those forms get no default and no range check: ask the user for a target. `story validate` warns `unused-target` until you do. Only set `count-unit: words` or `count-unit: characters` when the user asks to count the other way. Then run `story reindex .`, `story wordcount . --write`, and `story check .`.

The other publishing metadata (`isbn`, `publisher`, `publication-date`, `description`, `keywords`, `subjects`, `copyright`, `cover-alt`, `ai-disclosure`) is optional and can wait until the book is ready to publish; the `publishing` skill fills it in. Do not ask for it at init.

The story id recorded in every registry is the kebab-case form of the title (`--dir` sets only the directory). A title with no ASCII letters or digits takes its story id from the folder name: a Cyrillic or Greek title is transliterated for the default folder (`Война и мир` goes in `voyna-i-mir`), and a title in a script with no transliteration table, such as Chinese, needs `--dir` with an ASCII folder name. The id is recomputed from the title on every run, so it changes whenever the title does: after editing `title` in `story.md`, run `story reindex .` to rewrite the id in every registry, `plot/timeline.md`, and `continuity/state.md`, or `story validate` fails with `story must be <new-id>`. For a folder-name id, a new title that gains any ASCII letter or digit (`Война и мир — том 2`) takes over the id (`2`), so prefer titles without them or reindex afterwards. `init` refuses an existing directory unless you pass `--force`; with `--force` it only creates missing starter files and never overwrites an existing `story.md`, registry, timeline, or `continuity/state.md`.

`init` also writes a `.gitignore` listing `dist/` (build output), `.story.lock`, leftover `.*.story-*.tmp` and `.story-*.tmp` files, and OS and editor swap files, but only when the project has none. It never edits an existing `.gitignore`; if it prints `note: .gitignore was kept and does not ignore dist/`, tell the user and offer to add a `dist/` line (or remove a `!dist/...` negation).

If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. Skills live in different places for each agent and install method, so do not guess a path: resolve `../story-maintenance/scripts/story.js` against the folder that holds this `SKILL.md`. With `<skills>` standing for the absolute path of the folder that holds this skill's folder, run the same `init` from the folder that will hold the new project, with each value quoted as above:

```shell
node <skills>/story-maintenance/scripts/story.js init '{Title}' --form '{form}' --genre '{genre}' --sub-genre '{sub-genre}' --setting-era '{era}' --pov '{pov-style}' --tense '{tense}' --synopsis '{synopsis}' --theme '{theme-1}' --theme '{theme-2}'
```

If neither `story` nor the bundled fallback can run (Node is missing, or the `story-maintenance` skill is not installed), create the files by hand from `references/manual-setup.md`, then continue with step 2.

2. Draft a working premise:

`story init` writes neither `premise` nor `counter-premise`, so add or fill in both in the `story.md` frontmatter by hand (a manual setup already wrote their keys, so never add a second pair), as quoted strings (`premise: "..."`), and reuse a `premise-workshop` premise if there is one. Fill in the `premise:` and `counter-premise:` fields as hypotheses, not commitments. The premise is a one-sentence controlling idea — value + cause, e.g. "justice triumphs because the hero outsmarts the system". The counter-premise is the antagonist's embodied argument: the story's opposing value, stated as the antagonist would believe it. Draft both early, alongside the synopsis, but do not force theme — a working premise is a guess to be audited, not a conclusion to be imposed. Revisit it during revision: the `revision-continuity` theme audit pass (see the `theme-craft` skill for the deep pass) checks whether the ending actually dramatizes the premise through consequence. If the draft argues a different premise, update the premise, not the draft.

3. Present a summary of what was created and suggest next steps:
   - "Workshop the premise" (triggers premise-workshop skill) if the premise is still a guess
   - "Add your first character" (triggers character-management skill)
   - "Start worldbuilding" (triggers worldbuilding skill)
   - "Define your plot structure" (triggers plot-structure skill)
   - "Set up the style sheet" (triggers voice-style skill) once there is a writing sample
   - "Run `story next .`" to show deterministic next actions

4. When CLI access is available, run the maintenance commands from inside the new project folder (`{story-title-kebab}/`, or the folder given to `--dir`). They matter most after creating the registries by hand:

```shell
story reindex .
story wordcount . --write
story check .
```

If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root.

## Reference Files

- **`references/title-logline.md`** - Title craft (comps, hook phrasing, title as promise) and the logline recipe
- **`references/manual-setup.md`** - The folder layout, `story.md` bible, and empty registries to write by hand when no Story CLI can run

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
