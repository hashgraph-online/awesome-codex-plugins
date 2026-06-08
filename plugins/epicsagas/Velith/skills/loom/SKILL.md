---
name: loom
description: "AI-native publishing system: autonomous multi-phase workflows from ideation to export. Fiction, non-fiction, and technical books. Trigger: /velith or book-related requests."
---

# Velith — AI-Native Publishing System

## Overview

Build books like software. 6-phase pipeline from blank page to published book, with dedicated skills, agents, and quality gates at every stage.

```
Phase 0: Onboarding → Phase 1: Ideation → Phase 2: Outlining → Phase 3: Drafting → Phase 4: Editing → Phase 5: Publishing
```

## Genre Support

| Genre | Key Differences | Reference File |
|-------|----------------|----------------|
| Fiction | Plot structure (Save the Cat!/Snowflake), character bible, scene beats | `book-fiction` |
| Non-Fiction | Problem-solution structure, persona-driven, evidence hierarchy | `book-nonfiction` |
| Technical | Concept progression (novice→expert), code examples, diagrams, API docs | `book-technical` |
| Screenplay | 3-act + sequence method, dialogue/action, A/B story | `book-screenplay` |
| Poetry | Form-driven (sonnet/haiku/free verse), imagery systems, collection arc | `book-poetry` |
| Game | Quest trees, branching dialogue, lore bible, flag system | `book-game` |
| Academic | IMRAD, literature review, argument chains, citation practices | `book-academic` |
| Custom | Compose patterns from any genre via `book-genre-creator` | `book-genre-creator` |

## Phase Router

When `/velith` is invoked without arguments, detect current project state and route:

1. **No project exists** → Run Phase 0 (Onboarding)
2. **Project exists, no outline** → Run Phase 1 (Ideation)
3. **Outline exists, no drafts** → Run Phase 2 (Outlining) validation, then Phase 3
4. **Drafts exist, incomplete** → Continue Phase 3 (Drafting)
5. **All drafts complete** → Run Phase 4 (Editing)
6. **Editing complete** → Run Phase 5 (Publishing)

Detection: check for `drafts/` directory, `outline.md`, `STYLE.md`, `PRD.md` in current project.

## Phase Details

### Phase 0: Onboarding (`/velith onboard`)
- Genre selection (fiction/non-fiction/technical/screenplay/poetry/game/academic/custom)
- Target audience definition
- Language selection
- Project directory setup
- Source material scan (existing notes, articles, code)
- Generate `STYLE.md` (voice, tone, conventions)
- Generate `PRD.md` (book requirements)

### Phase 1: Ideation (`/velith ideate`)
- Market research (competing titles, gaps)
- Core concept distillation (elevator pitch)
- Unique value proposition
- Scope definition (chapters, word count, timeline)
- Save to `ideation.md`

### Phase 2: Outlining (`/velith outline`)
- Generate full chapter outline with dependencies
- Per-chapter specs: title, hook, key concepts, word target, difficulty level
- Cross-chapter reference map
- Save to `outline.md`
- Agent: `book-architect` validates structure

### Phase 3: Drafting (`/velith draft`)
- Plan-Then-Execute pattern: chapter-by-chapter generation
- Each chapter gets: outline context + previous chapter summary + style guide
- Parallel chapter generation via subagents (max 4 concurrent)
- Agent: `scene-generator` decomposes chapters into scenes first (fiction only)
- Agent: `chapter-writer` generates each chapter (from scenes if available)
- Agent: `continuity-editor` checks cross-chapter consistency
- Quality gate: line count, frontmatter, style compliance

### Phase 4: Editing (`/velith edit`)
- 5-stage editing pipeline:
  1. Editorial Assessment (macro structure)
  2. Developmental Edit (flow, pacing, gaps)
  3. Line Edit (sentence-level clarity)
  4. Copy Edit (grammar, consistency)
  5. Proofread (final typos)
- Agent: `style-doctor` enforces voice consistency
- Generate editing report with severity-ranked issues

### Phase 5: Publishing (`/book-publish`)
- Format conversion (EPUB/PDF/MOBI/TXT/MD via Pandoc + Calibre)
- Agent: `cover-designer` → concepts + image prompts
- Agent: `marketing-expert` → launch strategy
- Metadata, title candidates, KDP checklist

## Project Structure

```
{project-dir}/
├── PRD.md              # Book requirements (Phase 0)
├── STYLE.md            # Voice, tone, conventions (Phase 0)
├── ideation.md         # Ideas, market research (Phase 1)
├── outline.md          # Full chapter outline (Phase 2)
├── drafts/             # Chapter drafts (Phase 3)
│   ├── ch00-foreword.md
│   ├── ch01-xxx.md
│   └── ...
├── edits/              # Editing reports (Phase 4)
│   └── editorial-report.md
├── publish/            # Final outputs (Phase 5)
│   ├── book.epub
│   ├── book.pdf
│   └── metadata.yaml
└── sources/            # Source material references
```

## Sub-Skills

Each phase has a dedicated skill in `skills/book-{name}/SKILL.md`:

| Skill | Phase | Description |
|-------|-------|-------------|
| `book-init` | 0 | Project setup, genre selection, STYLE.md + PRD.md |
| `book-ideation` | 1 | Market research, concept distillation, scope |
| `book-outline` | 2 | Chapter outline with dependencies and cross-references |
| `book-draft` | 3 | Plan-Then-Execute chapter generation |
| `book-edit` | 4 | 5-stage editing pipeline |
| `book-publish` | 5 | EPUB/PDF/MOBI packaging, cover, marketing |
| `book-status` | — | Project status dashboard and web UI |
| `book-fiction` | — | Fiction patterns (Save the Cat!, character bible) |
| `book-nonfiction` | — | Non-fiction patterns (problem-solution, persona) |
| `book-technical` | — | Technical book patterns (concept progression, code) |
| `book-screenplay` | — | Screenplay patterns (3-act + sequence method, dialogue) |
| `book-poetry` | — | Poetry patterns (form types, imagery systems, collection) |
| `book-game` | — | Game scenario patterns (quest trees, branching, lore) |
| `book-academic` | — | Academic patterns (IMRAD, lit review, argument chains) |
| `book-genre-creator` | — | Meta-skill for genre selection and custom genre creation |

## Agents

| Agent | Role | When |
|-------|------|------|
| `book-architect` | Structure validation, outline generation | Phase 2 |
| `chapter-writer` | Chapter draft generation | Phase 3 |
| `continuity-editor` | Cross-chapter consistency check | Phase 3-4 |
| `style-doctor` | Voice and tone consistency | Phase 4 |
| `scene-generator` | Scene-level breakdown with GMC+RDD (fiction only) | Phase 3, fiction |
| `cover-designer` | Cover concepts + image generation prompts | Phase 5 |
| `marketing-expert` | Reader personas, channel strategy, launch calendar | Phase 5 |

## Quality Gates

Each phase has mandatory completion criteria before proceeding:

| Phase | Gate | Evidence |
|-------|------|----------|
| 0 | Project initialized | PRD.md + STYLE.md exist |
| 1 | Concept validated | Elevator pitch + 3 competing titles analyzed |
| 2 | Outline complete | All chapters specified + cross-reference map |
| 3 | Drafts complete | All chapters meet word target + frontmatter |
| 4 | Editing complete | 5-stage pipeline passed + <5 issues remaining |
| 5 | Publish ready | EPUB/PDF generated + metadata complete |

## Integration with Existing Tools

- **alcove**: Search existing project docs as source material
- **episteme**: Validate technical content against knowledge graph
- **discover**: Run problem discovery for book concept
- **council**: Get multi-voice input on structure/outline decisions
