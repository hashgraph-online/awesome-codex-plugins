---
name: research
description: This skill should be used when the user asks to "research", "fact-check", "check the history", "is this accurate", "research notes", "sources", "historical accuracy", "technical accuracy", "how would this really work", "verify a detail", "interview an expert", "plan a site visit", "expert review", or needs to investigate and record the real-world facts a story relies on and the chapters that use them.
---

# Research

## Overview

Investigate the real-world facts a story depends on and keep them in
`research/` notes: the question, a search plan, the findings with a
citation for each, how confident the finding is, and the chapters that
rely on them. Research is active work, not only a ledger: form precise
questions, go to primary sources where they exist, interview people and
visit places, and record what was found in a form a later fact-check can
retrace.

The CLI tracks each note's status (`open`, `verified`, `disputed`), its
`used-in` chapters, and the optional `accuracy`, `confidence`, `method`,
`risk`, and `reviewed-by` fields. It checks the chapter links, warns when a
final chapter still rests on research that is open or disputed, and warns
when a risky note reaches a final chapter without a qualified reviewer.

## Prerequisites

A story project with `story.md` in the root. The `research/` folder and its
registry are created by the first `story add research`.

## When to Use

- A chapter depends on history, science, law, medicine, a trade, a real
  place, or any detail a knowledgeable reader could check
- The user asks whether something is accurate
- Before marking a chapter `final` in historical, technical, or
  contemporary fiction
- NOT for invented world facts (use `worldbuilding`) or story-internal
  continuity (use `revision-continuity`)

## Workflow

### 1. Open a note

```shell
story add research 'Tidal bore timing' --used-in chapter-03 \
  --accuracy must-be-accurate --method fact --confidence low
```

Fill the note's `## Question` with what the story needs to get right, in
one or two sentences. Set the fields that describe the note:

- `accuracy` - how closely the prose must match reality:
  `must-be-accurate` (a checkable real fact the plot or setting relies
  on), `blended` (real facts deliberately mixed with invention), or
  `invented` (a made-up fact recorded here for consistency). Invented notes
  need no sources and never trigger the open-research warning.
- `method` - where the knowledge comes from: `fact` (desk research),
  `reading` (a book or paper read for background), `interview`,
  `site-visit`, or `expert-review`.
- `confidence` - `high`, `medium`, or `low`; how sure the current findings
  are. Start at `low` and raise it as sources agree.
- `risk` - a list, when getting it wrong could harm a reader, a real person,
  or the author: `legal`, `medical`, `weapons`, `safety`, `cultural`,
  `defamation`, `technical`. Pass `--risk` once per value.

### 2. Plan the investigation

1. Break the question into the specific things the prose asserts or
   implies ("Could she walk from the station to the docks in 20 minutes in
   1953?" rather than "1950s Liverpool").
2. Write a short `## Search Plan` in the note: the terms to search, the
   archives, records, or reference works to try, and the people who would
   know. Mark which would be primary sources (records, first-hand accounts,
   official data, the place itself) and which secondary.
3. Decide what "enough" looks like: one authoritative primary source, or
   two independent secondary sources that agree.

### 3. Research

1. Use the research tools available in the session (web search or fetch,
   documents the user provides). If none are available, give the user the
   search plan and ask them to supply sources.
2. Record each finding under `## Findings` with its citation beside it:
   author or institution, title, date, and the page, section, or URL.
   When a finding rests on exact wording, quote it and give the page or
   URL, so the claim can be retraced without repeating the search. Add
   every source to the `sources` frontmatter list, one full citation or
   URL per entry, with `--source` on `story add` or by editing the file.
3. Set `confidence` from the evidence: `high` for a primary source or
   independent agreement, `medium` for one good secondary source, `low`
   for anything recalled, inferred, or from a single weak source.
4. **Never present unverified knowledge as verified.** A fact recalled
   without a source stays `status: open`. Only set `status: verified` when
   every finding the chapters rely on has a source. Set `status: disputed`
   when sources disagree, and record both sides.
5. For interviews and site visits, prepare questions and consent first and
   record notes in the note body; see
   `references/interviews-and-site-visits.md`.

### 4. Flag risk; never advise

Notes with any `risk` value need a qualified human reviewer (a lawyer,
clinician, weapons or safety specialist, cultural reader, or subject
engineer, as fits) before the chapters that use them are final. Record the
reviewer in `reviewed-by` as a name or role once they have read the
passage. `reviewed-by` is a list with no `story add` flag; edit the note's
frontmatter by hand:

```yaml
reviewed-by:
  - "Dr A. Patel, A&E consultant"
```

Collect facts and flag concerns, but **never give legal, medical,
or safety advice yourself**, and never treat your own research as the
review. Portrayals of real, living people carry defamation risk; route
those, and sensitivity or authenticity reads, through the
`editorial-review` skill.

### 5. Connect it to the story

1. List every chapter that relies on the note in `used-in`. A chapter not
   written yet is fine (`chapter-09` before it exists), but `story links`
   still reports a typo of an existing chapter (`chapter-1` beside
   `chapter-01`) or `chapter-00` as missing.
2. Under `## Story Use`, record how the prose uses the facts and any
   deliberate departure from them (compressed timelines, invented
   institutions). A recorded departure is a choice, not an error.
3. Revise the chapters if the findings contradict them, following the
   `revision-continuity` skill.

### 6. Before finalising

Run `story validate .`: it warns about a `final` or `complete` chapter that
uses open or disputed research, about verified notes with no sources, and
about notes with a `risk` used in a final or complete chapter with no
`reviewed-by`. Resolve those before the chapter is marked final, or tell
the user which facts remain unverified and which reviews are outstanding.

## Conventions

- Note ids are kebab-case topics: `research/tidal-bore-timing.md`.
- `sources` entries are kept whole, so citations may contain commas.
- `used-in` lists chapter ids. `story move`, `story split`, and
  `story merge` rewrite them when chapters are renumbered, split, or
  merged, and `story remove chapter` takes the removed chapter out.
  `story rename` never changes a chapter id.
- `accuracy: invented` notes are a consistency record, not research; keep
  invented world facts that belong to the setting in `worldbuilding`.
- Sensitive or lived-experience topics need a human reader as well as
  sources. Suggest an authenticity or sensitivity read through the
  `editorial-review` skill, record the reader in `reviewed-by`, and triage
  their notes through the `feedback-triage` skill.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the
bundled fallback `node ../story-maintenance/scripts/story.js` with the same
arguments. Use `node <checkout>/bin/story.js` instead only when the user
names a Story Skills repository checkout or you are working in one. Write
the script as an absolute path (resolve the fallback relative to this skill
folder) and run it from the folder you would run `story` from, so `.` and
other relative paths keep their meaning. Use Node, not Bun or a package
script: Bun would load that folder's `bunfig.toml` (which can run code) and
`.env`, and a package script runs from the checkout's root. If no CLI is
available, keep the `used-in` lists current by hand, and leave the
`research/_index.md` table to the next `story reindex .`: never edit its
rows.

After adding or editing research notes:

```shell
story reindex .
story wordcount . --write
story check .
```

## Reference Files

- **`references/research-practice.md`** - What to check, search plans, how to judge sources, citing quotes, confidence, accuracy levels, risk flags, and deliberate departures
- **`references/interviews-and-site-visits.md`** - Preparing questions, consent, recording notes, and turning interviews and visits into research notes

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
