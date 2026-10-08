# Story Conventions

These conventions apply across all story skills. Every `SKILL.md` links here and repeats a one-line summary, so a skill installed on its own without `story-maintenance` still has the essentials. `docs/concepts.md` explains them for users, and `docs/project-format.md` is the full schema reference.

## Files and identifiers

- **Kebab-case filenames** for all entity files (e.g., `sera-voss.md`, `ashen-citadel.md`)
- **YAML frontmatter** on every file in a story project for structured metadata (a standalone piece saved outside a project, such as a single poem, needs none)
- **Schema version** - `story.md` frontmatter includes `schema-version: 2`
- **Character identifiers** use the kebab-case filename without extension (e.g., `sera-voss`)
- **Scene identifiers** use `chapter-{NN}-scene-{NN}` and live in `scenes/`

## Project files

- **`_index.md`** registries list each domain's entities. `story reindex` rebuilds their tables from the entity files, and `story add`, `rename`, `move`, and `remove` reindex for you. Never add or edit a registry row by hand, even without the CLI: change the entity file and reindex. Reindex keeps the hand-written sections, which are yours to edit: `## Relationship Map` and `## Family Trees` in `characters/_index.md`, `## World Overview` in `worldbuilding/_index.md`, and `## Story Structure`, `## Theme Tracking`, and the `structure` field in `plot/_index.md`
- **`story.md`** is the top-level bible read by all skills for context
- **`style-sheet.md`** records voice and house style; skills that write or revise prose read it
- **Continuity state** lives in `continuity/state.md`, with open questions, promises, and clues tracked under `continuity/questions/`, `continuity/promises/`, and `continuity/clues/`

## Setups, payoffs, and story time

Each setup and each event has one record. Update that record, and never copy it into another:

- **A mystery clue or red herring** - `continuity/clues/{id}.md` (`story add clue`), checked by `story clues` and `story continuity`
- **Any other setup the reader is owed a payoff on** (a Chekhov's gun, a vow, a prophecy, a deadline) - `continuity/promises/{id}.md` (`story add promise`), checked by `story continuity`
- **A question the reader is left asking** - `continuity/questions/{id}.md` (`story add question`), checked by `story continuity`
- **A hint inside one arc that needs no checked payoff** (an image, a motif, an echo) - a row of that arc's `## Foreshadowing` table. `story check` only checks that its `chapter-NN` ids exist (and `move` and `split` rewrite or guard them); nothing checks its status or payoff. A clue or promise never gets a row there too
- **When a drafted scene happens** - the scene's `date` and `time`, which `story timeline` orders and `story continuity` checks
- **Backstory and planned events** - `plot/timeline.md`, the hand-kept plan. Once an event is drafted, set its `Chapter` cell; the scene's `date` and `time` then say when it happens, so do not add a plan row for each drafted scene

A promise or clue moves from `planned` to `planted` (with `planted: chapter-{NN}`) to `paid-off` (with `payoff: chapter-{NN}`); a question moves from `open` to `answered` (with `resolved: chapter-{NN}`).

## Links and casts

- **Bidirectional cross-links** - when referencing another entity, update both files
- **Death tracking** - when a character dies on the page, set `status: deceased` and `died-in: chapter-{NN}` so `story continuity` can flag posthumous appearances
- **`mentions` vs `characters`** - chapter and scene frontmatter lists characters present in-scene under `characters`; characters who are only referenced, remembered, recorded, or seen in flashback go under `mentions`

## Maintenance

- **One maintenance block, one order** - after adding, removing, renaming, or revising story files, run `story reindex .`, then `story wordcount . --write`, then `story check .` (which runs `validate`, `links`, and `continuity` and fails only on errors). Run any skill-specific check, such as `story clues .` or `story pacing .`, after it.

## Scripts

- **Markdown-first artifacts** - create and edit story content directly in the target `.md` files. Do not create project-local build scripts, generator scripts, or bulk writer scripts (for example `build-*.js`) to emit story files.
- **Single-quote the user's words** - a title, name, synopsis, paragraph label, or other text from the user goes into a `story` command in single quotes, never in double quotes, where the shell still runs `$(...)` and backticks and expands `$name`. The skills write these values as `'{Title}'` or `'<name>'`. How to write a single quote inside the value depends on the shell:
  - POSIX shells (bash, zsh, sh, Git Bash): end the quote, add an escaped quote, and reopen it, `'\''` (`story add character 'Mara O'\''Neill'`).
  - PowerShell: double it (`story add character 'Mara O''Neill'`). The POSIX form is a syntax error there, and a value with an unescaped `'` ends the string early, so PowerShell would run the rest as a command.
  - cmd.exe: single quotes do not group words, and `&`, `|`, and `^` act even inside a value, so do not run a command with user text there. Use PowerShell or a POSIX shell.
- **CLI helpers stay external** - the only JavaScript helper agents should run is the installed or bundled Story CLI (`story`, or `story-maintenance/scripts/story.js` or a Story Skills checkout's `bin/story.js` run with Node from the folder `story` would run in) for deterministic maintenance. Do not copy it into the user's story project, and remove any unavoidable scratch helper before finishing.
