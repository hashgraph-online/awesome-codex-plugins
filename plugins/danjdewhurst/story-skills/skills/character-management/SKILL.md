---
name: character-management
description: This skill should be used when the user asks to "create a character", "update a character", "add a character", "build a family tree", "character relationships", "character timeline", "character arc", "character profile", "relationship graph", "name a character", or needs to manage characters in a story project. NOT for recording or checking character voices (use voice-style), rewriting dialogue so the voices differ (use line-editing), or a thematic arc's lie, truth, and arc type (use theme-craft).
---

# Character Management

## Overview

Create and manage rich character profiles for a story project. Each character is a markdown file with YAML frontmatter in the `characters/` directory. Characters are cross-referenced with other story elements through kebab-case identifiers.

## Prerequisites

A story project must already exist (created via the story-init skill). Verify by checking for `story.md` in the project root.

## Creating a Character

1. Read `story.md` for genre, themes, and tone context
2. Read `characters/_index.md` for existing characters
3. Ask for the character's name and role (protagonist, antagonist, supporting, minor, narrator, deuteragonist). Before settling the name, run `story names '{Name}'` (several candidates can be checked at once): it errors on an exact clash with any existing character, alias, location, faction, artifact, system, or glossary term, and warns about look-alikes and names sharing an initial with a major character. Invented names from a culture should follow its naming rules (see `references/naming-languages.md` in the `worldbuilding` skill)
4. Build the profile through conversation, exploring:
   - Appearance and distinguishing features
   - Personality, traits, and quirks
   - Backstory and formative events
   - Motivations (external wants vs internal needs)
   - Voice and speech patterns (ask for example dialogue), plus `voice-words` (words and phrases they reach for) and `voice-avoid` (words they would never say)
   - Pronunciation, when the name is invented or easily misread (`pronunciation: "SEER-sha"`)
   - Character arc (starting state, turning points, ending state)
   - Key life events for the timeline
5. Write the character file using the template in `references/character-template.md`
6. Save to `characters/{name-kebab}.md`, or use `story add character '{Name}' --role '{role}'` when the CLI is available. Cyrillic and Greek names are transliterated (`Пётр` gives `characters/petr.md`). When the name is in a script with no transliteration table (`李明`), or the user wants a different spelling, choose the ASCII id yourself and pass it: `story add character '李明' --id li-ming --role supporting` keeps `name: 李明` in the file
7. Leave the `characters/_index.md` table to the CLI: `story add` and `story reindex .` rebuild it from the character files, so never add a row by hand
8. If relationships reference existing characters, update those character files too
9. When CLI access is available, run the maintenance pass in the story root:

```shell
story reindex .
story wordcount . --write
story check .
```

## Updating a Character

1. Read the existing character file
2. Read `characters/_index.md` for context on other characters
3. Make the requested changes. If the change happens partway through the story (a scar, a new title, a turn to the other side), add a progression instead of editing the opening value (see Changes Over the Story)
4. If relationships changed, update the other character's file (bidirectional)
5. Change a role or status in the character file only. The `characters/_index.md` table picks it up at the next `story reindex .`, so never edit its rows
6. When CLI access is available, run `story reindex .`, `story wordcount . --write`, and `story check .`

## Changes Over the Story

A character file describes the character as the story opens. Record a change that happens in a later chapter as a progression, so an agent drafting an earlier chapter does not write it in too soon:

```yaml
progressions:
  - from: chapter-10
    field: scar
    value: "Jaw to collarbone, taken holding a door"
  - from: chapter-14
    field: role
    value: antagonist
```

- `from` is the first chapter where the new value holds. It may be a planned `chapter-NN` with no file yet
- `field` is kebab-case. It can be an existing single-value field (`status`, `role`, `arc`) or a new one (`scar`, `title`). List fields (`aliases`, `relationships`, `locations`, `tags`, voice lists) cannot change this way; record a shifted relationship as a progression on its own field, such as `field: standing-with-kael` with `value: estranged` under `progressions`, never as a top-level field (that would show from chapter 1)
- `value` is one value. `role` and `status` values must be ones the character file allows
- Keep entries in story order. Do not use a progression alone for a death: set `died-in` (see below). A `status` progression is still checked against the story: `story continuity` warns when a progression to `deceased` with no `died-in` is followed by the character in a cast or learning something, when a status progression brings them back between `died-in` and `revived-in`, and when a progression to `deceased` still holds at `revived-in`
- Before drafting or revising a chapter, run `story knowledge {id} --at chapter-NN`. It lists what the character knows at that chapter in story time (by date when both chapters are dated, otherwise by chapter number), the same rule as `story context`, and which progressions already apply. Write to that state rather than the opening frontmatter alone
- A line marked `reader-knowledge` is already on the page, or known before the book, and may appear in the prose. A line marked `character-knowledge` and `do not reveal` is something the character knows from a flashback the reader has not reached: the character may act on it, and the fact itself must not be stated. Do not drop those lines, and do not write them in as if the reader had already learned them

After adding or editing progressions, run `story reindex .`, `story wordcount . --write`, and `story check .`.

## Renaming or Killing Off a Character

To rename:

1. Check the new name with `story names '{New Name}'`, and list where the prose uses the old one with `story mentions character {id}`.
2. Preview with `story rename character {id} '{New Name}' --prose --dry-run`. It prints each replacement in drafted chapter prose (`file:line:column: old → new`) and the files it would change. The full name becomes the new name, the given name alone becomes the new given name, and possessives keep their `'s`. Aliases and nicknames are left as written; outlines, HTML comments, code fences, link and image targets, HTML tags, reference definitions, and URLs are never touched, and an initial (the `J` of `J. R. Dunn`) is not a given name. It refuses a name, or a new given name, that another entity (cut characters included) already uses; pick another name or ask the user.
3. Show the user the replacements before running it for real, then run the same command without `--dry-run`. It also sets `name`, renames the file when the id changes, and rewrites the id in every frontmatter field and markdown link target.
4. After the summary line, it lists matches it left as written, each with its reason: a word that may be an ordinary word (`May` of May Dunn, which may be the month, or a name opening a sentence in a chapter that also uses the word in lower case), or the text of a reference link whose label is defined (`[Ines]` with `[ines]: …`). Read each one and edit it by hand if it means this character; for a reference link, keep the old label (`[Ruth][Ines]`) so the link still works. A `prose-name-shared` warning lists places another entity shares the name, which were left alone: treat them the same way. Update any alias that should change in the character file and in the prose yourself.
5. Hand-written registry sections (such as Family Trees in `characters/_index.md`), link labels, and outline beats keep the old display name: search for it (`grep -rn "Old Name" .`) and update each hit by hand.
6. Run `story reindex .`, `story wordcount . --write`, and `story check .`.

Without `--prose`, `rename` leaves the chapter text alone, for when the user wants to revise those passages by hand.

To kill a character off:

1. Set `status: deceased` and `died-in: chapter-NN` in the character file
2. In every later chapter and scene, move the id from `characters` (and `pov`) to `mentions` where they appear only in memory, letters, or flashback
3. Run `story continuity .`: it reports any later chapter or scene that still lists them in its cast

Variants:

- **Planned death:** set `died-in` to an outline chapter and keep `status: alive`; set `status: deceased` when that chapter is drafted
- **Dead narrator (ghost, posthumous POV):** keep them as `pov` and also list them in `mentions`; that is not a posthumous appearance
- **Resurrection:** add `revived-in: chapter-NN`; casts from that chapter on are allowed again, and once it is drafted set `status: alive`. If a progression made them `deceased`, add a `status` progression from the revival chapter too
- **Second death after a resurrection:** keep `died-in` and `revived-in` on the first death and revival, and add a `status` progression to `deceased` from the chapter where they die again. `died-in` holds only one death, and `revived-in` already brings them back, so no progression to `alive` is needed. Once that chapter is drafted, `status: deceased` is correct; while it is an outline, keep `status: alive`
- **Non-linear books:** give chapters a `date` so deaths compare by story time, and give a dual-timeline book's chapters a `strand` so each timeline keeps its own clock and its own route check
- Drop the character's `character-state` entry in `continuity/state.md` once the death is drafted and at or before `current-chapter`

After either change, run `story reindex .`, `story wordcount . --write`, and `story check .`.

## Managing Relationships

Reference `references/relationship-types.md` for the full list of relationship types and inverse pairs.

When adding a relationship:
- Add the relationship entry to the character's frontmatter
- Add the inverse relationship to the other character's frontmatter
- Update the Relationship Map section in `characters/_index.md`

## Family Trees and Relationship Graphs

Generate the relationship graph from character frontmatter instead of drawing it by hand:

```shell
story diagram relationships
story diagram relationships --out dist/relationships.mmd
```

It prints Mermaid source built from every character's `relationships`, with family edges styled distinctly so the family tree stands out from alliances and rivalries. Each pair gets one edge: parent, grandparent, aunt, and uncle draw an arrow from the elder side, other types draw an undirected line, and child-side types (child, grandchild, niece, nephew) are skipped, so the diagram cannot show a one-way relationship. GitHub, many editors, and mermaid.live render it. Use it to spot isolated characters and families missing a generation, and run `story links` to find one-way relationships and missing backlinks; regenerate it after relationship changes rather than editing the output.

Family trees are also maintained in the `characters/_index.md` under the "Family Trees" section. Format:

```markdown
## Family Trees

### {Family Name}
- **{Character Name}** ({status}) - [{Name}]({name-kebab}.md)
  - **{Child Name}** - [{Name}]({name-kebab}.md)
  - **{Child Name}** - [{Name}]({name-kebab}.md)
```

Indent children under parents. Note marriages/partnerships inline.

## Voice Fields

`voice-words` and `voice-avoid` are optional lists in character frontmatter that make a speaker's voice checkable:

```yaml
voice-words:
  - "reckon"
  - "love"
voice-avoid:
  - "awesome"
  - "literally"
```

Here "love" is a term of address ("all right, love"). Keep notes like that in prose, not as `#` comments in frontmatter; the parser keeps them as part of the value.

`story voices .` fingerprints each character's attributed dialogue (see the `voice-style` skill for how lines are attributed) and warns when they say a `voice-avoid` word, when a `voice-words` entry never appears, and when two characters' voices are near-identical. Keep these lists short (three to eight entries) and consistent with the Voice & Speech Patterns section and the style sheet's Character Voices line (see the `voice-style` skill).

This skill sets a voice when it builds the profile. Recording and checking voices across the book belongs to the `voice-style` skill, and rewriting dialogue so two voices differ belongs to the `line-editing` skill.

## Cross-Referencing

- When a character is referenced in worldbuilding (e.g., a location's `notable-characters`), ensure the link exists both ways
- Character-location backlinks live in the character file's `locations` frontmatter list
- Faction memberships live in `worldbuilding/factions/{faction-kebab}.md` under `members`
- Artifact ownership can reference a character id in `worldbuilding/artifacts/{artifact-kebab}.md`
- When a character appears in a plot arc, ensure they're listed in the arc's `characters` frontmatter
- Character tags should be consistent across the project (e.g., if `magic-user` is used, always use that exact tag)

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, perform the registry, backlink, and word-count checks manually.

## Reference Files

- **`references/character-template.md`** - Full blank template for character profiles, including the Antagonist Design section. The lie, truth, ghost-wound, and arc-type fields belong to `theme-craft`
- **`references/relationship-types.md`** - Complete relationship type reference with inverse pairs
- **`references/ensemble-cast.md`** - Managing multi-character casts: anchor character, A/B/C story braiding, thematic relevance, merge-characters discipline
- **`references/supporting-characters.md`** - Role vocabulary (mentor, foil, confidant, love interest, comic relief, threshold guardian) and requirements for supporting roles

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
