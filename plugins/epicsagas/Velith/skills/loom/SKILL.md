---
name: loom
description: "Velith router. Detects book project state and runs the next phase of the 6-phase pipeline (onboarding → ideation → outlining → drafting → editing → publishing) to the human-quality bar. Trigger: /loom, /velith, or any book-writing request."
argument-hint: "[onboard|ideate|outline|draft|edit|publish|status] [--force]"
---

# Velith — Books to the Human-Quality Bar

Velith produces books a cold reader cannot distinguish from a competent human author's work. Six phases, ten agents, one standard: `quality-bar.md` in this directory. Read it once per session before doing any writing or editing work.

`${CLAUDE_PLUGIN_ROOT}` is this plugin's install directory. On hosts that do not substitute it, use the directory that contains `velith.mjs`.

## Operating principles (supersede earlier Velith conventions)

1. **Full-manuscript context.** Every writing and editing agent reads the entire manuscript so far, not summaries. Frontier models carry 1M tokens; a novel is under 200K. Voice drift and contradictions come from partial context. `bible.md` is an index and ledger, not a substitute for reading.
2. **Sequential drafting for narrative work.** Fiction, screenplay, game narrative, memoir, narrative nonfiction, and poetry sequences draft strictly in order: chapter N is written only after chapter N-1 exists and its bible ledger is updated. Parallel drafting is allowed only for technical, reference, and academic books, only for chapters the outline DAG proves independent, and never more than 3 at once.
3. **Voice lock before volume.** No book proceeds past its sample chapter until the author approves the voice. Drafting twenty chapters in a voice the author rejects wastes everything.
4. **Draft, critique, revise.** No chapter is saved after a single pass. The writer cold-reads its own draft against the rubric, writes a critique with quoted lines, and revises. Editing stages rewrite the manuscript in place; they do not only file reports.
5. **Grounded claims.** Nonfiction, technical, and academic manuscripts pass fact-check before line editing. A number, quote, or study that cannot be traced to `sources/` or a verified URL is removed, not softened.
6. **Reader gate.** Phase 4 ends with a cold read by simulated target readers. Publishing requires a PASS verdict or an explicit author override.
7. **One look per book.** Images follow `art-bible.md` the way prose follows `STYLE.md`. Prompts are compiled from it, diagrams and drawings are code-rendered, every image passes vision QA, and a look lock precedes volume. See `book-visuals`.
8. **Author checkpoints.** The pipeline stops for the author at six points: concept selection, outline approval, voice lock, look lock (if the book has images), developmental restructures, and readiness verdict. Everything else runs without asking.

## Phase router

Run `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan <project-dir>` to get project state, then route:

| State | Route |
|-------|-------|
| No `PRD.md` | Phase 0 `/book-init` |
| `PRD.md` but no `ideation.md` and no `outline.md` | Phase 1 `/book-ideation` |
| `ideation.md` but no `outline.md` (or outline lacks `## Approval`) | Phase 2 `/book-outline` |
| `outline.md` + `bible.md`, no drafts | Phase 3 `/book-draft` (starts with voice lock) |
| Drafts exist, `STYLE.md` lacks `## Voice Lock` | Phase 3 voice lock step, then continue drafting |
| Drafts incomplete | Phase 3 `/book-draft` (resume) |
| All chapters drafted, no `edits/readiness-report.md` with `verdict: PASS` | Phase 4 `/book-edit` |
| Readiness PASS, no `publish/book.epub` | Phase 5 `/book-publish` |
| Everything present | Report status; offer `/book-illustrate`, re-edit, or new project |

With an explicit argument (`/loom draft`), run that phase regardless of detection, but still enforce the gates: drafting refuses to run without an approved outline; publishing refuses without readiness PASS unless `--force`.

## Phases at a glance

| Phase | Skill | Agents | Author checkpoint | Exit artifact |
|-------|-------|--------|-------------------|---------------|
| 0 Onboarding | `book-init` | — | — | `PRD.md`, `STYLE.md` (with voice fingerprint), `sources/INDEX.md` |
| 1 Ideation | `book-ideation` | — | Concept selection | `ideation.md` with chosen concept + reader promise |
| 2 Outlining | `book-outline` | `book-architect` | Outline approval | `outline.md` (approved), `bible.md` |
| 3 Drafting | `book-draft` | `scene-generator` (fiction), `chapter-writer`, `continuity-editor` | Voice lock | `drafts/ch*.md`, `bible.md` ledger, `.velith/critiques/` |
| 4 Editing | `book-edit` | `fact-checker` (nonfiction), `continuity-editor`, `style-doctor`, `beta-reader` | Developmental restructures, readiness verdict | `edits/01-06*.md`, revised `drafts/`, `edits/readiness-report.md`, `edits/editorial-report.md` |
| 3-5 Visuals | `book-visuals` | `art-director`, `figure-engineer`, `illustrator`, `cover-designer` | Look lock | `art-bible.md`, `visuals/` |
| 5 Publishing | `book-publish` | `cover-designer`, `marketing-expert` | — | `publish/` bundle |

## Genre support

| Genre | Skill | What it adds |
|-------|-------|--------------|
| Fiction (all subgenres) | `book-fiction` | Structure options, scene craft, character depth, the fiction-specific tells |
| Nonfiction | `book-nonfiction` | Argument architecture, evidence discipline, the nonfiction tells |
| Technical | `book-technical` | Concept gradient, runnable code, failure-first teaching |
| Screenplay | `book-screenplay` | Format, sequence method, dialogue subtext |
| Poetry | `book-poetry` | Form, line, collection architecture |
| Game narrative | `book-game` | Branching, quest design, lore bible |
| Academic | `book-academic` | IMRAD, citation integrity, argument chains |
| Custom | `book-genre-creator` | Compose a genre spec from the above |

Agents read the genre skill for the project's genre (`${CLAUDE_PLUGIN_ROOT}/skills/book-{genre}/SKILL.md`) at the start of every task. Custom genres read `genre-custom.md` in the project.

## Agents

| Agent | Phase | Job in one line |
|-------|-------|-----------------|
| `book-architect` | 2 | Turns concept into an approved outline and a bible; scores structure |
| `scene-generator` | 3 (fiction) | Plans scenes for one chapter: purpose, turn, subtext, exit. Plans, not prose |
| `chapter-writer` | 3 | Drafts one chapter in full context, critiques it, revises it, updates the bible |
| `continuity-editor` | 3-4 | Finds contradictions and repetitions across the whole manuscript against the bible |
| `fact-checker` | 4 (nonfiction) | Builds a claim ledger, verifies every fact, removes what cannot be verified |
| `style-doctor` | 4 | Measures and rewrites: AI tells, voice drift, rhythm uniformity |
| `beta-reader` | 4 | Cold reads as target readers; issues the readiness verdict |
| `art-director` | 2-5 | Writes the art bible, runs the look lock, reviews every image with vision, signs off the contact sheet |
| `figure-engineer` | 3-5 | Code-rendered diagrams, charts, technical drawings, maps' base layers, ornaments |
| `illustrator` | 3-5 | Diffusion illustrations from the art bible with compiled prompts and vision QA |
| `cover-designer` | 5 | Cover concepts from the art bible, formats, marketing variants |
| `marketing-expert` | 5 | Positioning, personas, launch calendar |

## Project structure

```
{project-dir}/
├── PRD.md              # Requirements + reader promise (Phase 0-1)
├── STYLE.md            # Voice fingerprint, rules, voice lock record (Phase 0, 3)
├── ideation.md         # Concepts, comps, chosen concept (Phase 1)
├── outline.md          # Approved chapter specs + dependency map (Phase 2)
├── bible.md            # Characters/concepts, world/term rules, timeline, per-chapter ledger (Phase 2+)
├── art-bible.md        # Visual identity: look, palette, constants, figure system, look lock (Phase 2+)
├── sources/            # Reference material + INDEX.md (Phase 0+)
├── drafts/             # ch{NN}-{slug}.md, ch{NN}-scenes.md (Phase 3); revised in place (Phase 4)
├── visuals/            # plan.md, manifest.json, figures/, illustrations/, photos/, ref/, prompts/
├── edits/              # 00-fact-check.md … 06-readiness-report.md, editorial-report.md (Phase 4)
├── publish/            # EPUB/PDF/etc., metadata, cover/, marketing (Phase 5)
└── .velith/            # status.json, art-bible.json, critiques/, snapshots/, metrics.json
```

## Status and tooling

- `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan <dir> [--ui]` — project state, dashboard data
- `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs metrics <file|dir>` — sentence/paragraph statistics, repeated phrases, AI-tell counts (JSON)
- `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs snapshot <dir> <label>` — copy `drafts/` to `.velith/snapshots/` before a rewriting stage
- `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs images compile|check|render <dir> [id]` — model-agnostic image prompts from the art bible, asset validation, figure rendering
- `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs agents <id> <running|complete|error> [task]` — agent status for the dashboard

Every skill ends with `scan` so the dashboard stays current.

## Integrations (optional)

- **alcove** — search the author's document vault as source material during `/book-init` and drafting.
- **humanize-korean** — if installed, style-doctor may run it as a final Korean polish after its own pass.
- **Image generation MCPs** — `cover-designer` and `illustrator` produce prompts; if an image tool is available they can execute them.
