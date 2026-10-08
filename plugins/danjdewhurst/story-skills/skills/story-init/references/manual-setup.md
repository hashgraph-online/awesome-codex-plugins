# Manual Setup

Create a story project by hand only when no Story CLI can run: `story` is not installed, and the bundled fallback that ships with the `story-maintenance` skill cannot run (Node is missing, or that skill is not installed). `story init` writes these same files, so prefer it whenever it runs. When the files are written, return to step 2 of `SKILL.md` and draft the working premise.

1. Create the folder structure at the current working directory:

```
{story-title-kebab}/
├── .gitignore
├── story.md
├── style-sheet.md
├── characters/
│   └── _index.md
├── worldbuilding/
│   ├── _index.md
│   ├── locations/
│   ├── systems/
│   ├── factions/
│   └── artifacts/
├── plot/
│   ├── _index.md
│   ├── arcs/
│   └── timeline.md
├── scenes/
│   └── _index.md
├── continuity/
│   ├── state.md
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
    └── _index.md
```

Write `.gitignore` only if the folder has none, with `dist/`, `.story.lock`, `.*.story-*.tmp`, `.story-*.tmp`, `.DS_Store`, `Thumbs.db`, `*.swp`, `*.swo`, and `*~`, one per line.

2. Populate `story.md` with the story bible:

```yaml
---
title: "{Title}"
schema-version: 2
genre: {genre}
sub-genre: {sub-genre}
setting-era: {era}
status: planning
form: {form}
themes:
  - {theme-1}
  - {theme-2}
premise: "{One-sentence controlling idea: value + cause, e.g. justice triumphs because the hero outsmarts the system}"
counter-premise: "{The antagonist's embodied argument}"
pov: {pov-style}
tense: {tense}
language: {language-tag}
---
```

Below the frontmatter, include sections:
- **Synopsis** - the 2-3 sentence synopsis provided
- **Tone & Style** - brief notes on the story's voice (derive from genre/themes)
- **Notes** - empty section for the user to fill in

3. Populate each `_index.md` with an empty registry:

**`characters/_index.md`:**
```markdown
---
type: character-registry
story: {story-title-kebab}
---

# Characters

## Registry

| Name | Role | Status | File |
|------|------|--------|------|
| *No characters yet* | | | |

## Relationship Map

*No relationships defined yet.*

## Family Trees

*No family trees defined yet.*
```

**`worldbuilding/_index.md`:**
```markdown
---
type: world-registry
story: {story-title-kebab}
---

# Worldbuilding

## World Overview

*Describe the world at a high level here.*

## Locations

| Name | Type | Region | File |
|------|------|--------|------|
| *No locations yet* | | | |

## Systems

| Name | Type | File |
|------|------|------|
| *No systems yet* | | |

## Factions

| Name | Type | Status | File |
|------|------|--------|------|
| *No factions yet* | | | |

## Artifacts

| Name | Type | Status | File |
|------|------|--------|------|
| *No artifacts yet* | | | |
```

**`plot/_index.md`:**
```markdown
---
type: plot-registry
story: {story-title-kebab}
structure: three-act
---

# Plot Structure

## Story Structure

**Model:** Three-Act Structure (adjust as needed)

## Arcs

| Name | Type | Status | File |
|------|------|--------|------|
| *No arcs yet* | | | |

## Theme Tracking

| Theme | Arcs | Chapters |
|-------|------|----------|
| *No themes tracked yet* | | |
```

**`plot/timeline.md`:**
```markdown
---
type: timeline
story: {story-title-kebab}
---

# Story Timeline

| When | Event | Arc | Chapter |
|------|-------|-----|---------|
| *No events yet* | | | |
```

**`chapters/_index.md`:**
```markdown
---
type: chapter-registry
story: {story-title-kebab}
---

# Chapters

## Registry

| # | Title | POV | Status | Word Count | File |
|---|-------|-----|--------|------------|------|
| *No chapters yet* | | | | | |

## Total Word Count: 0
```

Also create the v2 support files. Every registry and `continuity/state.md` needs `story: {story-title-kebab}` in addition to its `type`, or `story validate` reports a missing `story` field:

- `scenes/_index.md` with frontmatter `type: scene-registry` and `story: {story-title-kebab}`
- `continuity/state.md` with frontmatter `type: continuity-state`, `story: {story-title-kebab}`, `current-chapter: 0`, and empty `character-state`, `object-state`, and `knowledge-state` lists
- `continuity/questions/_index.md` with frontmatter `type: question-registry` and `story: {story-title-kebab}`
- `continuity/promises/_index.md` with frontmatter `type: promise-registry` and `story: {story-title-kebab}`
- `continuity/clues/_index.md` with frontmatter `type: clue-registry` and `story: {story-title-kebab}`
- `glossary/_index.md` with frontmatter `type: glossary-registry` and `story: {story-title-kebab}`
- `style-sheet.md` (optional) with frontmatter `type: style-sheet`, `dialect: unspecified`, and empty `preferred`, `watch-words`, and `allow-words` lists, plus the body sections described in the `voice-style` skill

If manual initialization gets tedious, stop and ask the user to install or run the Story CLI rather than inventing a different project shape.
