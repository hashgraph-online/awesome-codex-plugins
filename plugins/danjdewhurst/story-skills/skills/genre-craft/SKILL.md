---
name: genre-craft
description: This skill should be used when the user asks about "mystery", "fair play", "clue", "red herring", "romance beats", "HEA", "thriller", "ticking clock", "horror", "dread", "MG", "YA", "middle grade", "young adult", "science fiction", "sci-fi", "fantasy", "quest", "chosen one", "historical fiction", "period voice", "anachronism", "comedy", "humour", "humor", "romcom", "farce", "satire", "running gag", "serial", "episodic", "web serial", "genre conventions", or wants genre-specific structural craft for a story project. NOT for a clue check as a revision pass (use revision-continuity).
---

# Genre Craft

## Overview

Genre-specific structural packs: the codified craft each genre expects, as
checkable rules, ledgers, and audits. Packs cover mystery (fair play + clue
ledger), romance (beats + HEA contract), thriller (ticking clock, power
imbalance, set pieces), horror (dread/terror ordering, monster rules),
MG/YA (category constraints), science fiction (load-bearing speculative
elements), fantasy (quest structure, magic paid off by its rules and costs),
historical fiction (period voice, anachronisms, real people), comedy
(escalation, comic set-ups and payoffs, tone), and serial/episodic
structure. Use at story-init (pick the pack, set the constraints) and in
revision (run the pack's audit).

## Prerequisites

A story project must already exist (created via the story-init skill) with
its genre recorded in `story.md`. A plot structure (plot-structure) should
exist or be in progress.

## When to Use

- Starting or re-categorizing a story in one of the covered genres
- Planning genre load-bearing elements (clues, clocks, season goals)
- Auditing a draft against its genre's contract
- NOT for line-level genre voice (that belongs to the `better-writing`
  skill's genre work); these packs are structural
- NOT for literary fiction as a pack — its conventions resist deterministic
  encoding by design

## Workflow

1. **Pick the pack.** Read `story.md` for genre/sub-genre and load the
   matching reference:
   - Mystery / crime / detective → `references/mystery-fair-play.md`
   - Romance → `references/romance-beats.md`
   - Thriller / action / suspense → `references/thriller.md`
   - Horror → `references/horror.md`
   - Middle grade / young adult → `references/mg-ya.md`
   - Science fiction → `references/scifi-pipeline.md`
   - Fantasy (epic, quest, secondary-world) → `references/fantasy.md`
   - Historical fiction → `references/historical.md`
   - Comedy (romantic comedy, farce, satire, cosy comedy) →
     `references/comedy.md`; a cosy mystery not played for laughs needs
     only the mystery pack
   - Serial / episodic / web serial → `references/serial-episodic.md`
   - Multi-genre stories: load each applicable pack; where packs conflict
     (e.g. horror's slow dread vs. thriller's cliffhangers), decide with
     the user which genre's contract dominates per section and record the
     decision in `story.md` notes.
2. **Set the constraints up front.** Apply the pack's structural
   requirements during planning:
   - Mystery: create `continuity/clues/` and ledger every clue and red
     herring via `story add clue '...' --planted chapter-NN --payoff
     chapter-NN`, with `significance-delayed` frontmatter where the reader
     sees the clue before understanding it and `red-herring: true` on
     misleading clues (`story add clue '...' --red-herring`; their
     `payoff` is the chapter that debunks them).
     Run `story clues .` for the fair-play matrix and `story diagram clues`
     for the plant-to-reveal flow.
   - Thriller: log every promised deadline in `continuity/promises/` and
     give every scene a `date` and `time`, so `story timeline .` shows the
     story clock.
   - Serial: record `season-goal:` in `story.md` and `episode-question:`
     in each installment's frontmatter, and the release cadence as
     `release-every:` (days, or months such as `1 month`) and
     `release-start:` (YYYY-MM-DD) in `story.md`, or `release-date:` on a
     chapter. `story next .` shows the next episode due and warns when one
     due within `release-warn-days:` (default 3) has no prose.
   - MG/YA: record `target-words:` in `story.md` and check the category
     constraints (protagonist age, minimized adult involvement).
   - Sci-fi: write the speculative element's rules, costs, and limits in
     `worldbuilding/systems/` before the climax exploits them.
   - Fantasy: write the magic's rules, costs, and limits in
     `worldbuilding/systems/` (the `worldbuilding` skill designs them) and
     log the quest goal and any prophecy in `continuity/promises/`.
   - Historical: record `setting-era` in `story.md`, the chosen period
     register in the style sheet, and a `research/` note (the `research`
     skill) for every fact the plot leans on and every real person; run
     the `editorial-review` real-people pass for anyone living or recently
     dead.
   - Comedy: record the comic sub-genre in `story.md`, the tone line (where
     comedy stops) in its `## Tone & Style` section, each comic lead's flaw
     in their character file, and each running gag or call-back the reader
     is owed a payoff on as one promise in `continuity/promises/`.
     Sentence-level comic timing belongs to the `line-editing` skill.
3. **Draft against the pack.** Use the pack's beat concepts and rules
   alongside the `chapter-writing` workflow and the `scene-craft`
   scene-grain tools. Cross-link thriller pacing to the Fichtean curve
   note in `references/thriller.md`, and check thriller and serial chapter
   endings with `story pacing .` (chapter `hook` values, and runs of
   `resolution` endings); cross-link serial book-level canon
   to the `series-continuity` skill.
4. **Run the pack audit in revision.** Each reference ends with an audit
   checklist. Run it as part of a developmental revision pass (see the
   `revision-continuity` skill) and record findings in the revision plan.
5. **Record genre decisions.** Any deliberate deviation from the pack (a
   romance without a black moment, a mystery that withholds) is a story
   decision: note it in `story.md` with the reason, so later audits don't
   "fix" it.

## Conventions

- Pack-specific entities use the project conventions: kebab-case ids,
  YAML frontmatter, `_index.md` registries where a collection exists
  (`continuity/clues/` follows the `continuity/promises/` pattern).
- Clue `planted` must precede `payoff` (`story continuity` flags payoff-before-
  plant as an error); deadline promises follow the same ordering logic as
  promise/question ordering.
- Clues carry the links: each clue names its `planted` and `payoff`
  chapters and, under `characters`, the suspects it implicates or clears,
  and `story links` checks those ids. Character files have no clue field;
  to list a suspect's clues, run
  `story list clues --where characters={character-id}`.
- Genre audits live in the revision plan or `continuity/` audit files —
  never only in chat.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, perform the registry, backlink, and word-count checks manually.

After adding or changing genre entities (clues, deadlines, comic set-ups,
season goals, episode questions):

```shell
story reindex .
story wordcount . --write
story check .
story clues .     # mystery: fair-play matrix and warnings
```

## Reference Files

- **`references/mystery-fair-play.md`** - Fair-play doctrine, clue-planting techniques, red-herring discipline (`red-herring: true`), gather-suspects reveal, clue ledger convention, the `story clues` fair-play matrix and `story diagram clues`
- **`references/romance-beats.md`** - Widely-published romance beat concepts (paraphrased), HEA/HFN reader contract, the black moment
- **`references/thriller.md`** - Ticking clock honored once promised, power imbalance, set pieces, mini-cliffhanger endings, Fichtean curve pairing
- **`references/horror.md`** - Dread vs. terror vs. gross-out ordering, the uncanny, monster rules stated early, recovery periods
- **`references/mg-ya.md`** - Word-count norms, age-appropriate voice/stakes, minimized adult involvement, content boundaries
- **`references/scifi-pipeline.md`** - Speculative element must be load-bearing, rules stated before exploited, worldbuilding→plot pipeline
- **`references/fantasy.md`** - Quest and journey structure, magic rules stated before the climax relies on them, cost and limits, secondary-world exposition, chosen-one pitfalls
- **`references/historical.md`** - Period voice vs. readability, anachronism checks (things, words, ideas), invented vs. real people, ethics of the real past, the author's note
- **`references/comedy.md`** - Escalation, reversals, comic set-ups and payoffs (call-backs, rule of three, running gags), character-driven humour (comic flaw, straight man and funny man, want vs. need), tone management and comic sub-genres; sentence-level timing handed to `line-editing`
- **`references/serial-episodic.md`** - Season/volume goal, per-episode dramatic question, a reward in every installment, recap discipline

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
