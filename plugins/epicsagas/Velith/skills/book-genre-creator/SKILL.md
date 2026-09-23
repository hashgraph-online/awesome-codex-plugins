---
name: book-genre-creator
description: "Meta-skill for genre selection and custom genre creation. Routes a project to the right built-in genre or composes a genre-custom.md spec from existing patterns, including agent behavior and validation rules."
argument-hint: "[list|custom]"
---

# Genre Creator

Use when the project does not fit a built-in genre cleanly, or when the author is unsure which genre applies. Read `${CLAUDE_PLUGIN_ROOT}/skills/loom/quality-bar.md` and the candidate genre skills.

## Built-in genres

| Genre | Skill | Core shape | Best for |
|-------|-------|-----------|----------|
| fiction | `book-fiction` | Three-act / 15-beat / bespoke; scene craft; character depth | Novels, novellas, short stories, web novels |
| non-fiction | `book-nonfiction` | Problem → principles → practice; evidence discipline | Business, self-help, essays, memoir, narrative nonfiction |
| technical | `book-technical` | Concept gradient + running project; failure-first | Programming, engineering, data science |
| screenplay | `book-screenplay` | Three-act + eight sequences; subtext | Film, TV, web series |
| poetry | `book-poetry` | Form, line, collection arc | Collections, chapbooks |
| game | `book-game` | Branching, quests, lore bible | Game scenarios, visual novels, interactive fiction |
| academic | `book-academic` | IMRAD / discipline structures; citation integrity | Theses, dissertations, monographs |

## Selection

Three questions, then route:

1. What is the reader doing with it? (living a story / learning to understand / learning to do / watching / playing / reading aloud / examining)
2. What does the author fear most going wrong? (boring middle / being wrong / being unclear / being obvious / being inconsistent)
3. What does "done" look like? (a bound book / a script / a build / a submission)

Hybrids are common: a memoir with a practical framework (nonfiction, narrative spine); a technical book with a fictional running story (technical, with fiction scene craft for the story sections); an illustrated poetry-essay (poetry + nonfiction). Most hybrids are a primary genre with a borrowed section from another; write that into `genre-custom.md` rather than inventing a new genre.

## Custom genre spec

Write `genre-custom.md` in the project root. Agents read it in place of a built-in genre skill.

```markdown
# Genre: {name}

## Parent genre
{closest built-in; agents read that skill first, then this file}

## Reader and what they are doing with it
...

## Structure
{shape with proportions; which chapters borrow which genre's craft}

## Borrowed craft
- From book-fiction: scene design for the narrative interludes
- From book-nonfiction: evidence discipline for the argument chapters

## Unique elements
{what no built-in genre covers}

## Tells to watch
{genre-specific failure modes, in addition to quality-bar.md}

## Validation
{what the architect scores; what beta-reader's personas are}

## Agent notes
| Agent | Behavior override |
|-------|-------------------|
| scene-generator | runs only on chapters tagged `narrative: true` in the outline |
| fact-checker | runs on argument chapters only |
```

## Agent behavior by genre

| Agent | fiction | non-fiction | technical | screenplay | poetry | game | academic |
|-------|---------|-------------|-----------|------------|--------|------|----------|
| book-architect | arc, midpoint, setup/payoff | promise map, evidence map | DAG, running project | beat pages, sequences | collection arc | branch map, flags | thesis chain, synthesis matrix |
| scene-generator | scene plans | — | — | beat sheets | — | quest/dialogue plans | — |
| chapter-writer | scenes in one voice | claim + evidence + story | build + break + explain | slug/action/dialogue | poems | quests + nodes | sections with citations |
| continuity-editor | characters, timeline, motifs | terms, recurring example, claims | prerequisites, code state | props, locations, time | imagery, form adjacency | flags, lore | terminology, citations |
| fact-checker | real-world claims only | full | full + runs code | real-world claims only | — | — | full + citation existence |
| style-doctor | voice, distance, tells | register, hedging, tells | clarity, jargon, tells | action-line economy | sound, compression | line length, barks | register, hedging |
| beta-reader | genre readers + one editor | target readers + one skeptic | target devs + one senior | reader + one producer | readers + one poet | players + one designer | peers + one examiner |
| art-director | character/setting constants, 0-4 ill./ch | figure system, photo policy | diagram grammar, screenshot policy | pitch tone board | narrowest palette, spot art only | map, sheets, branching maps | discipline figure conventions |
| figure-engineer | maps (fantasy) | charts, concept diagrams | architecture/sequence/state diagrams | season-arc diagram | — | maps, branching flowcharts | data figures |
| illustrator | scenes, headers, sheets | rarely | never | key art | section spots | key art, sheets | never |
| cover-designer | genre visual language | category conventions | tech aesthetic | poster | literary | key art | press style |
| marketing-expert | Goodreads, BookTok, 리디 | LinkedIn, newsletters, 브런치 | Dev.to, HN, GitHub | festivals, competitions | readings, 문예지 | Steam, itch, communities | conferences, journals |

## Usage

`/book-genre-creator` runs selection. `/book-genre-creator list` shows the table. `/book-genre-creator custom` starts the spec. If `PRD.md` already has a genre, show that genre's workflow and offer to customize.
