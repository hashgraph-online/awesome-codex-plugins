---
name: worldbuilding
description: This skill should be used when the user asks to "create a location", "add a location", "magic system", "political system", "build the world", "add culture", "world history", "technology system", "religion", "economy", "map", "travel times", "routes", "calendar", "moons", "seasons", "naming language", "conlang names", "trade routes", "supply lines", "magic cost", "add a glossary term", "glossary", "invented word", or wants to develop any aspect of a story's world and setting. NOT for a glossary for translators (use adaptation).
---

# Worldbuilding

## Overview

Create and manage world elements for a story project. Locations, systems (magic, politics, technology, etc.), factions, and artifacts are stored as markdown files in the `worldbuilding/` directory with YAML frontmatter, and glossary terms for the world's invented words in `glossary/terms/`. All elements cross-reference characters and other story elements.

## Prerequisites

A story project must already exist (created via the story-init skill). Verify by checking for `story.md` in the project root.

## Creating a Location

1. Read `story.md` for genre, era, and tone context
2. Read `worldbuilding/_index.md` for existing locations and systems
3. Ask for the location's name and type (city, fortress, wilderness, etc.)
4. Build the location through conversation, covering:
   - Physical description and atmosphere
   - History relevant to the story
   - Culture and customs of inhabitants
   - Notable features characters will interact with
   - Current state at story's timeline
   - Routes to other locations: travel time in hours and mode (see `references/maps-and-routes.md`)
   - Pronunciation, if the name is invented or easily misread (`pronunciation: "KEL-ah-mar"`)
5. Before settling an invented name, run `story names '{Candidate}'` to catch clashes and look-alikes (see `references/naming-languages.md`)
6. Create it with `story add location '{Location Name}' --type '{type}'` when the CLI is available (add `--region`, `--population`, `--controlled-by`, and `--character` as known); it writes `worldbuilding/locations/{name-kebab}.md` and lists it in `worldbuilding/_index.md`. Then fill the body from `references/location-template.md`
7. Without the CLI, write the file from `references/location-template.md` to `worldbuilding/locations/{name-kebab}.md`
8. Leave the locations table in `worldbuilding/_index.md` to `story reindex .`, even without the CLI; never add a row by hand
9. If notable characters are listed, verify those character files exist and add this location's kebab-case identifier to each character file's `locations` frontmatter list
10. When CLI access is available, run `story reindex .`, `story wordcount . --write`, and `story check .`

## Maps, Routes, and Travel

Record travel between locations as `routes` on the location file, not in prose notes, so the CLI can check it:

```yaml
routes:
  - to: harbor-district
    hours: 1.5
    mode: on foot
  - to: saltmarsh-fort
    hours: 9
    mode: coach
```

- `to` is a location id; `story links .` checks it exists.
- A route is two-way unless the other location declares its own route back (for example, uphill slower than down).
- `story continuity .` errors when a character appears in two dated scenes at locations joined by a route and the story time between them is shorter than the route's `hours`.
- `story diagram locations` prints the route network as a Mermaid map-graph with edges labelled in hours; add `--out dist/locations.mmd` to save it. Use it to spot unreachable places and implausible shortcuts.

Use the travel speeds table in `references/economy-logistics.md` to set plausible hours, and `references/maps-and-routes.md` for the full workflow.

## Creating a System

1. Read `story.md` for genre and themes context
2. Read `worldbuilding/_index.md` for existing systems
3. Identify the system type and consult `references/world-element-types.md` for the relevant prompts. For calendars, naming languages, economies, and magic costs, also use `references/calendars.md`, `references/naming-languages.md`, and `references/economy-logistics.md`
4. Build the system through conversation, addressing the key questions for that type
5. Create it with `story add system '{System Name}' --type '{type}' --prevalence '{prevalence}'` when the CLI is available (the type and prevalence values are in `references/system-template.md`); it writes `worldbuilding/systems/{name-kebab}.md` and lists it in `worldbuilding/_index.md`. Then fill the body from `references/system-template.md`
6. Without the CLI, write the file from `references/system-template.md` to `worldbuilding/systems/{name-kebab}.md`
7. Leave the systems table in `worldbuilding/_index.md` to `story reindex .`; never add a row by hand
8. Cross-reference with characters who interact with the system (e.g., magic-users for a magic system)
9. When CLI access is available, run `story reindex .`, `story wordcount . --write`, and `story check .`

## Creating A Faction

Use `story add faction '{Faction Name}' --type '{family|guild|government|military|religion|company|community|criminal|other}'` when the CLI is available. Otherwise create `worldbuilding/factions/{name-kebab}.md` with frontmatter fields `name`, `type`, `status`, `members`, `locations`, and `tags`.

Cover:
- Purpose and ideology
- Power base, resources, and territory
- Important members
- Conflicts and pressure points

Then:
1. Save to `worldbuilding/factions/{name-kebab}.md`
2. Leave the Factions table in `worldbuilding/_index.md` to `story reindex .`; never add a row by hand
3. If members are listed, verify those character files exist
4. When CLI access is available, run `story reindex .`, `story wordcount . --write`, and `story check .`

## Creating An Artifact

Use `story add artifact '{Artifact Name}' --type '{object|weapon|document|technology|relic|symbol|resource|other}'` when the CLI is available. Otherwise create `worldbuilding/artifacts/{name-kebab}.md` with frontmatter fields `name`, `type`, `status`, `owner`, `location`, and `tags`.

Cover:
- Description and recognition details
- Function, constraints, and costs
- History and prior owners
- Current owner/location state

Then:
1. Save to `worldbuilding/artifacts/{name-kebab}.md`
2. Leave the Artifacts table in `worldbuilding/_index.md` to `story reindex .`; never add a row by hand
3. If an owner or location is listed, verify those files exist and cross-reference back
4. When CLI access is available, run `story reindex .`, `story wordcount . --write`, and `story check .`

## Adding A Glossary Term

Record an invented word, title, rank, or concept that the prose must spell and use the same way every time as a glossary term in `glossary/terms/`.

1. Read `glossary/_index.md` for the existing terms, then run `story names '{Term}'` to catch a clash with another name or term
2. Use `story add term '{Term}' --category '{person|place|faction|artifact|concept|term|other}'` when the CLI is available, with `--alias '{Variant}'` once for each accepted variant; it writes `glossary/terms/{term-kebab}.md` and lists it in `glossary/_index.md`. Otherwise create the file with frontmatter fields `term`, `category`, and `aliases`, and leave the `glossary/_index.md` table to `story reindex .`
3. Fill `## Definition` (what it means in the story) and `## Usage Notes` (spelling, capitalisation, who uses it, and what it never means). Add a `pronunciation` when the term is invented or easily misread
4. When the term's capitalisation or hyphenation is a house-style decision, record it in `style-sheet.md` too (see the `voice-style` skill)
5. When CLI access is available, run `story reindex .`, `story wordcount . --write`, and `story check .`

A glossary for translators belongs to the `adaptation` skill, which adds a `## Translations` section to these term files.

## Updating World Elements

1. Read the existing file
2. Make the requested changes. If a location or faction changes partway through the story (a city falls, a guild disbands), add a progression instead of editing the opening value (see Changes Over the Story)
3. If cross-references changed, update the linked files
4. Rename an element with `story rename` (see `references/naming-languages.md`). Change its type or status in its own file only: the `worldbuilding/_index.md` tables pick it up at the next `story reindex .`, so never edit their rows
5. When CLI access is available, run `story reindex .`, `story wordcount . --write`, and `story check .`

## Changes Over the Story

Location and faction files describe the world as the story opens. Record a later change as a progression, so drafting an early chapter does not see what happens in a late one:

```yaml
progressions:
  - from: chapter-10
    field: status
    value: occupied
  - from: chapter-10
    field: controlled-by
    value: lord-maren
```

- `from` is the first chapter where the new value holds. It may be a planned `chapter-NN` with no file yet
- `field` is a kebab-case single-value field, existing (`status`, `controlled-by`, `region`) or new (`ruler`, `population-note`). List fields (`notable-characters`, `routes`, `members`, `locations`, `tags`) cannot change this way
- `value` is one value. A faction's `type` and `status` must stay within their allowed values
- Keep entries in story order, and read the progressions up to the chapter being drafted before describing the place or faction in it
- Artifacts and systems do not take progressions; track an artifact's changes with `object-state` and scene `state-changes` (see the revision-continuity skill)

After adding or editing progressions, run `story reindex .`, `story wordcount . --write`, and `story check .`.

## Cross-Referencing

- Locations reference characters via `notable-characters` in frontmatter
- Characters reference locations via `locations` in frontmatter
- Factions reference character members and locations
- Artifacts reference an owner character or faction and a current location
- Systems reference practitioners via character tags
- Location `routes` reference other locations by id
- Invented names across characters, locations, systems, factions, artifacts, and glossary terms may carry a `pronunciation`; `story build --format narration` gathers them into a pronunciation guide for audiobook narrators
- When a location is used in a chapter, the chapter's frontmatter `locations` field links back
- Keep the `worldbuilding/_index.md` world overview section current as elements are added

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, perform the registry, backlink, and word-count checks manually.

## Reference Files

- **`references/location-template.md`** - Template for location files
- **`references/system-template.md`** - Template for system files
- **`references/faction-template.md`** - Template for faction files
- **`references/artifact-template.md`** - Template for artifact/object files
- **`references/world-element-types.md`** - Detailed prompts for each system type (magic, political, technology, religion, economic, military, social)
- **`references/maps-and-routes.md`** - Recording `routes`, the `story diagram locations` map-graph, and the continuity travel check
- **`references/calendars.md`** - Adding a custom `calendar` to `story.md`, dating scenes in it, and recording seasons and moons as a system file
- **`references/naming-languages.md`** - Phonology sketches, naming rules per culture, pronunciation, and the `story names` collision check
- **`references/economy-logistics.md`** - Prices and wages, supply lines, magic and technology costs, and a travel speeds table by mode

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
