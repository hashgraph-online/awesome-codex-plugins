---
name: theme-craft
description: This skill should be used when the user asks about "theme", "controlling idea", "thematic argument", "moral argument", "thematic arc", "flat arc", "negative arc", "the lie", "antagonist design", "motif", "symbolism", "theme audit", or wants to plan, track, or revise the thematic layer of a story, including the lie, truth, ghost-wound, and arc-type fields of a character file. NOT for finding or testing a story premise (use premise-workshop), or a character's profile, relationships, or "character arc" record (use character-management).
---

# Theme Craft

## Overview

Plan and audit theme as a working mechanism, not decoration. Covers the
controlling idea (value + cause, in McKee's sense), the lie/truth machinery
and the three canonical arc types, antagonist design as the embodied
counter-argument, motif tracking, and a revision-time theme audit. Use at
story start (working premise), during character design (lie/truth/arc-type),
and after a complete draft (theme audit).

## Prerequisites

A story project must already exist (created via the story-init skill).
Character files (character-management) and a plot structure
(plot-structure) should exist or be in progress.

## Workflow

1. **Draft the working premise.** Read `story.md` for genre and themes.
   Consult `references/controlling-idea.md` and write a one-sentence
   premise (value + cause) and counter-premise. Store them in `story.md`
   frontmatter:

   ```yaml
   premise: "{Value} triumphs because {cause}."
   counter-premise: "{Opposing value} triumphs because {opposing cause}."
   ```

   If the user prefers discovering theme in the draft, record
   `premise: tbd-discovery` and skip to step 3.
2. **Build the lie/truth machinery.** For the protagonist and antagonist
   (and any significant supporting character whose arc touches the theme),
   consult `references/lie-truth.md` and add to their character files:

   `arc-type` is one of `change-positive`, `change-negative`, or `flat`.
   Do not put that list in an inline comment: a command that rewrites the
   field drops the comment.

   ```yaml
   arc-type: change-positive
   lie: "{The false belief}"
   truth: "{The belief that resolves it}"
   ghost-wound: "{The specific backstory event that planted the lie}"
   ```

   Check the character's turning points against the arc-type guidance:
   flat arcs need escalating tests of steadfastness, not growth beats;
   negative arcs need the truth visibly refused.
3. **Design the antagonist as the counter-argument.** Consult
   `references/antagonist-design.md`: give the antagonist an edge, a
   defensible belief in the counter-premise, a want/wound/plan, and
   scenes they win. When the opposition is institutional, personify it.
4. **Plant motifs.** Consult `references/motif-symbolism.md`; choose two or
   three concrete motifs, plant them literally, and track plantings,
   variations, and ending resonance in the motif ledger.
5. **Use the premise while drafting.** When a scene decision is unclear, ask
   which choice engages the value continuum and costs the protagonist
   something. Feed the lie into scene sequels (see the `scene-craft`
   skill): the sequel is where the lie gets examined.
6. **Run the theme audit in revision.** After a complete draft, consult
   `references/theme-audit.md`: trace the value through the draft, check
   the ending against the opening's value-question, verify theme is
   dramatized through consequence not commentary, and confirm motifs are
   paid off. Record findings in `continuity/theme-audit.md` with a
   `theme-holds` / `theme-broken` verdict. Hand structural findings to the
   `revision-continuity` skill as a developmental revision plan.

## Conventions

- `premise:` / `counter-premise:` live in `story.md` frontmatter and are the
  single source of truth for the story's theme; `plot/_index.md` theme
  tracking maps themes to arcs and chapters as before.
- Character `arc-type` values are kebab-case from the fixed set
  (`change-positive`, `change-negative`, `flat`); `lie`, `truth`, and
  `ghost-wound` are one-line strings.
- Motif ids are kebab-case and tracked in the motif ledger with
  `planned` / `planted` / `paid-off` status.
- Theme is dramatized through choices and consequences. Never add a
  character speech, narration summary, or mentor lecture *explaining* the
  theme to satisfy an audit finding — rework the choices instead.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, perform the registry, backlink, and word-count checks manually.

After adding or changing premise fields, character arc fields, or the theme
audit:

```shell
story reindex .
story wordcount . --write
story check .
```

The motif ledger (`continuity/motifs.md` or the motif table in an arc file)
and `continuity/theme-audit.md` are prose revision notes: the CLI does not
scan, validate, link-check, or reindex them. Audit motif payoff and the
theme verdict manually per `references/theme-audit.md`.

## Reference Files

- **`references/controlling-idea.md`** - The controlling idea as value + cause (McKee), counter-premise, working-premise workflow
- **`references/lie-truth.md`** - Lie, truth, ghost wound, and the three arc types (change-positive, change-negative, flat)
- **`references/antagonist-design.md`** - Worthy opponent, antagonist as counter-argument, plan-the-antagonist-as-protagonist, personified institutions
- **`references/motif-symbolism.md`** - Plant-and-vary, object-symbol resonance with the ending, motif ledger
- **`references/theme-audit.md`** - Revision audit: ending vs. opening value-question, consequence vs. commentary, motif payoff

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
