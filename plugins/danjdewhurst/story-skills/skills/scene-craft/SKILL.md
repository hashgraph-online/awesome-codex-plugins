---
name: scene-craft
description: This skill should be used when the user asks to "plan a scene", "scene structure", "sequel scene", "dialogue subtext", "deep POV", "psychic distance", "try fail", "scene cards", "exposition", "info dump", "flashback", "time skip", "story opening", "first page hook", "introduce a character", "scene outcome", "yes-but no-and", "chapter hook", or wants scene-level craft for drafting or revision. NOT for book-level pacing or act structure (use plot-structure), or drafting the prose of a scene or chapter (use chapter-writing).
---

# Scene Craft

## Overview

Plan and check scenes at the scene grain — the layer between plot beats and
chapter prose. Covers the missing half of the chapter-writing scene model
(Scene **and** Sequel), try/fail escalation, scene cards, dialogue subtext,
deep POV and psychic distance, exposition handling, flashbacks and time
skips, and openings. Use during chapter planning, before drafting, and in
revision when a scene feels flat.

## Prerequisites

A story project must already exist (created via the story-init skill), with
characters defined (character-management) and a plot structure in place
(plot-structure). This skill extends chapter-writing; it does not replace the
outline-first drafting workflow.

## Workflow

1. **Choose the craft layer.** Identify which scene-grain problem this is:
   - Scene feels like incidents with no breathing room → `references/scene-sequel.md`
   - Middle of the chapter sags or resolves too easily → `references/try-fail.md`
   - Chapter has multiple POVs/timelines to order → `references/scene-cards.md`
   - Conversation reads flat or voices blur → `references/dialogue-subtext.md`
   - Narration feels distant or head-hops → `references/deep-pov.md`
   - Worldbuilding facts are piling up undelivered → `references/exposition.md`
   - Past events or a time jump are needed → `references/flashbacks-time.md`
   - Starting the book or a chapter, or introducing a character → `references/openings.md`
2. **Read the relevant reference(s).** Each file carries its own checklists
   and planning fields; apply them, don't paraphrase them. Read `language`
   in `story.md` (a missing field means `en`) and plan and draft in that
   language. The structural tools (scene and sequel, try/fail, scene
   cards, psychic distance) apply in any language; the word lists and
   dialogue-tag advice in `deep-pov.md` and `dialogue-subtext.md` are
   English, so for another language look for the same effect in that
   language and take dialogue punctuation from the style sheet.
3. **Clarify missing inputs before planning or editing.** Ask the user for
   any required inputs you cannot establish from the project files — scene
   purpose, viewpoint, location, canon-changing intent, and the applicable
   craft layer. Never guess at these or proceed on assumptions; a wrong
   guess edits canon. Only continue to step 4 once every required input
   is known.
4. **Plan before prose.** For the scene in question, write the planning
   inputs the reference requires (sequel beats, try/fail positions, subtext
   wants, zoom level, exposition audit, flashback trigger, hook check) into
   the chapter outline or the scene's planning notes before drafting or
   revising.
5. **Record machine-readable state.** Update the scene file in `scenes/`:
   - Set `outcome:` to how the scene's goal resolves for the POV
     character: `yes`, `no`, `yes-but`, or `no-and` (see
     `references/try-fail.md`). Prefer the complicating `yes-but` and
     `no-and`; a run of clean `yes` outcomes drains tension
   - Set `sequel: true/false` and fill the `dilemma:` field plus the
     `## Sequel` section (reaction/dilemma/decision) for scenes with
     sequel content (see `references/scene-sequel.md`)
    - Add `flashback-to:` (freeform note of the flashed-back moment,
      validated as a scalar by `story validate` but not used by continuity
      checks) and move flashback-only characters to `mentions`. A dated
      flashback warns `timestamp runs backward`; record that finding in
      `continuity/exemptions.md` rather than changing the date (see
      `references/flashbacks-time.md`)
   - Set `date:` (`YYYY-MM-DD`) and `time:` (`"HH:MM"` or `dawn`,
     `morning`, `midday`, `afternoon`, `evening`, `night`) once the
     scene's moment is settled, and `travel-hours:` (a number) when the
     POV character had to travel since the previous scene. Undated scenes
     switch off the clock and route checks in `story continuity` without
     a warning, except a scene with `travel-hours` above 0, which warns;
     `story timeline` shows what is still undated
   - Keep `state-changes` current for every change the scene makes
   - When the scene ends its chapter, set the chapter's `hook:` to how the
     chapter ends: `cliffhanger`, `question`, `revelation`, `reversal`,
     `decision`, `emotional`, or `resolution` (see `references/openings.md`
     for the first-page counterpart)
6. **Run the reference's checklist** against the draft or the revision plan
   (try/fail checklist, deep-POV filter-word scan, tag-swap test, first-page
   hook check). If `story prose` reports the filter-word check skipped for
   the book's language, do that scan by reading. Run `story pacing .` to see scene outcomes, sequel counts,
   and chapter hooks across the book: it warns after three or more
   consecutive `yes` outcomes, four or more scene units without a sequel,
   and three or more chapters in a row ending on `resolution`.
7. **Hand off cleanly.** Scene/sequel planning feeds the chapter-writing
   drafting workflow. When a scene decision changes canon (new knowledge,
   moved objects, changed relationships), update `continuity/state.md`
   and the affected entity files (bidirectional links, per the shared
   story conventions).

## Conventions

- Scene ids stay `chapter-{NN}-scene-{NN}`; scene files live in `scenes/`
  with kebab-case filenames.
- All planning metadata (dilemma, decision, subtext wants, psychic-distance
  level) lives in frontmatter or a `## Planning` / `## Scene Card` section
  of the scene file — never only in chat.
- `characters` vs `mentions` follows the story-init rule: characters present
  in-scene under `characters`; remembered, recorded, or flashback-only
  characters under `mentions`.
- Do not overwrite chapter prose merely to satisfy a craft checklist. Flag
  intentional deviations (e.g. a deliberate info dump as a stylistic device)
  in the scene file's planning notes so a later audit doesn't "fix" them.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, perform the registry, backlink, and word-count checks manually.

After adding or revising scene records:

```shell
story reindex .
story wordcount . --write
story check .
story pacing .
```

## Reference Files

- **`references/scene-sequel.md`** - Sequel mechanics: reaction → dilemma → decision (Dwight Swain's scene framework)
- **`references/try-fail.md`** - Try/fail escalation cycles, scene `outcome` values (yes/no/yes-but/no-and), and the Five Commandments scene shape
- **`references/scene-cards.md`** - Scene card unit (start state → change → end state), reordering, POV braiding
- **`references/dialogue-subtext.md`** - Subtext as planning input, dialogue-as-negotiation, voice differentiation, tag-swap test
- **`references/deep-pov.md`** - Psychic distance zoom levels and checkable deep-POV rules
- **`references/exposition.md`** - Drip-feed, conflict-carried exposition, in-world documents, info-dump warning
- **`references/flashbacks-time.md`** - Flashback entry/exit mechanics, tension-cheat warning, time-skip conventions
- **`references/openings.md`** - In medias res, "enter late, leave early", first-page hook check, character introduction technique

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
