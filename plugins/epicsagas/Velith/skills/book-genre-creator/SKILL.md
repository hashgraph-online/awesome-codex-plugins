---
name: book-genre-creator
description: "Meta-skill that references all available genres, agents, and skills to help users define and create any genre — including custom genres not yet supported."
---

# Genre Creator

## Purpose

Help users discover the right genre for their project, or define a completely new genre by composing patterns from existing ones. This is the entry point when the user's project doesn't fit neatly into an existing category.

## Supported Genres (built-in)

| Genre | Skill | Core Structure | Best For |
|-------|-------|---------------|----------|
| fiction | `book-fiction` | Save the Cat! 15-beat, Snowflake, Hero's Journey | Novels, novellas, short stories |
| non-fiction | `book-nonfiction` | Problem-solution, evidence hierarchy | Business, self-help, essays |
| technical | `book-technical` | Novice→expert progression, code blocks, labs | Programming, engineering, data science |
| screenplay | `book-screenplay` | 3-act + sequence method, dialogue/action | Film, TV, web drama scripts |
| poetry | `book-poetry` | Form-driven (sonnet/haiku/free verse), imagery | Poetry collections, anthologies |
| game | `book-game` | Quest trees, branching dialogue, lore bible | Game scenarios, visual novels, RPGs |
| academic | `book-academic` | IMRAD, literature review, argument chains | Thesis, dissertation, research papers |

## Genre Selection Guide

Ask the user these questions to route to the right genre:

1. **What are you creating?** (novel / textbook / screenplay / game story / poem collection / thesis / other)
2. **Who is the primary audience?** (readers / players / reviewers / students / viewers)
3. **What matters most?** (plot & characters / logical argument / visual storytelling / interactive branching / aesthetic form)

Routing:
- Plot & characters → fiction
- Logical argument + evidence → non-fiction or academic
- Visual storytelling → screenplay
- Interactive branching → game
- Aesthetic form / rhythm → poetry
- Code & hands-on practice → technical

## Custom Genre Creation

When the user's project doesn't match any built-in genre:

1. **Identify the primary pattern** — which built-in genre is closest?
2. **Identify divergences** — what's different about this project?
3. **Compose a hybrid structure** — mix patterns from relevant genres
4. **Define validation rules** — what does "done" look like for this genre?
5. **Save as genre spec** — write to `genre-custom.md` in the project directory

Custom genre spec template:

```markdown
# Genre: {name}

## Parent Genre
{closest built-in genre}

## Structural Template
{chapter/section/scene structure with percentages}

## Key Patterns (from built-in genres)
- From {genre}: {specific pattern}
- From {genre}: {specific pattern}

## Unique Elements
{what makes this genre different}

## Validation Rules
- {rule 1}
- {rule 2}

## Agents Used
{which agents from the pool are relevant, and any genre-specific adjustments}
```

## Agent Mapping by Genre

All genres can use these agents. This table shows genre-specific behavior:

| Agent | fiction | non-fiction | technical | screenplay | poetry | game | academic |
|-------|---------|-------------|-----------|------------|--------|------|----------|
| book-architect | 15-beat validation | problem-solution check | progression gradient | sequence validation | collection arc | branch map check | argument chain |
| chapter-writer | hook-conflict-turn-cliffhanger | hook-problem-evidence-framework-summary | hook-concept-code-explain-pitfalls-summary | slug-action-dialogue-beat | image-turn-resonance | quest steps + dialogue nodes | topic-evidence-analysis-link |
| scene-generator | GMC+RDD scenes | — | — | beat sheets | — | quest breakdown | — |
| continuity-editor | character/timeline | term consistency | prerequisite order | prop/location/time | imagery consistency | lore/flag consistency | citation/terminology |
| style-doctor | voice/tone (STYLE.md) | voice/tone | voice/tone | voice/tone | meter/voice | voice/tone | academic tone |
| cover-designer | fiction trends | non-fiction trends | tech trends | film poster style | artistic/poetic | game art style | academic press |
| marketing-expert | Goodreads/BookTok | LinkedIn/podcasts | Dev.to/HN | festivals/competitions | readings/literary mags | gaming communities | conferences/journals |

## Phase Adaptation by Genre

Not all genres use the same phase flow:

| Phase | fiction | non-fiction | technical | screenplay | poetry | game | academic |
|-------|---------|-------------|-----------|------------|--------|------|----------|
| 0. Onboarding | genre + audience + language | same | same | same | form selection | platform + engine | discipline + citation style |
| 1. Ideation | concept + market | same | same | logline + comps | theme + forms | core loop + hook | research gap + questions |
| 2. Outlining | chapter-by-chapter | same | same | sequence outline | collection arc | quest map + branch chart | chapter outline + lit review plan |
| 3. Drafting | scenes → chapters | chapters | chapters + code | sequences → scenes | poems (parallel) | quests + dialogues | sections (lit review → methodology → findings) |
| 4. Editing | 5-stage pipeline | same | same | dialogue polish + format check | line-level craft | playtest notes + branch verification | peer review + citation check |
| 5. Publishing | EPUB/PDF/KDP | same | same | PDF + Final Draft export | chapbook/EPUB | game doc bundle | PDF + journal submission |

## Usage

```
/book-genre-creator          → Interactive genre selection and setup
/book-genre-creator list     → Show all supported genres with descriptions
/book-genre-creator custom   → Start custom genre creation wizard
```

When invoked, read the project's PRD.md if it exists. If genre is already set, show the genre-specific workflow. If not, run the selection guide.
