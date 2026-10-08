---
name: revision-continuity
description: This skill should be used when the user asks to "revise a chapter", "continuity check", "find inconsistencies", "audit character state", "check timeline consistency", "developmental edit", "structural revision", "reverse outline", "cut a subplot", "revision passes", "what pass next", "pacing check" as a revision pass, "clue check", "cut to a word count", or "length pass", or to prepare existing story material for the next revision pass. NOT for planning book structure (use plot-structure), scene-level craft (use scene-craft), voice consistency (use voice-style), or reconciling a chapter drafted by discovery (use discovery-drafting).
---

# Revision Continuity

## Overview

Revise existing Story Skills projects without losing continuity. Use this skill for targeted chapter edits, continuity audits, developmental revision, line edits, and pre-flight checks before drafting the next chapter.

## Prerequisites

A story project must already exist. Verify by checking for `story.md` in the project root, then run or inspect `story report .` when CLI access is available. Read `story.md` `language` (a missing field means `en`) and write every revision in that language; when a `story prose` or `story voices` check is reported as skipped for the language, do that check by reading.

## Named Revision Passes

Track a full revision as a ladder of named passes in `story.md`
`revision-passes`, so the work happens in order (big structural changes
before polishing sentences that may be cut) and survives between sessions:

```shell
story passes . --init            # writes the default ladder, keeping existing entries
story passes .                   # checklist with the checks each pass runs
story passes . --start pacing    # mark a pass in-progress
story passes . --done pacing     # mark it done
story next .                     # with story status revising, recommends the next unfinished pass
```

The default ladder is `structure`, `character`, `theme`, `continuity`,
`pacing`, `line`, `copyedit`, `proof`. Each entry is `{pass, status}` with
status `pending`, `in-progress`, or `done`; add a custom kebab-case pass
(`fact-check`, `length`, `sensitivity`) with `story passes . --start <name>`, which
appends it as `in-progress`. The checks per pass, as `story passes .`
prints them, and the checklists in `references/pass-checklists.md` that
each pass works through:

| Pass | Checks | Checklists |
|------|--------|----------------|
| `structure` | `story timeline .`, `story pacing .`, `story diagram arcs` | Reverse outline, pacing waveform, removability audit |
| `character` | `story voices .`, `story knowledge <id> --at <chapter>`, `story diagram relationships` | Developmental revision (motivation, arcs) |
| `theme` | `story report .` | Theme audit |
| `continuity` | `story continuity .`, `story clues .`, `story links .` | Continuity audit, reveal economy, fact check |
| `pacing` | `story pacing .` | Pacing waveform |
| `line` | `story prose .`, `story voices .` | Line edit (the `line-editing` skill) |
| `copyedit` | `story prose .` + `style-sheet.md` | Copyedit (the `line-editing` skill) |
| `proof` | `story build --format print`, `story build --format html` | Proof (the `line-editing` skill) |

Mark a pass `--start` when beginning it and `--done` only when its checks
are clean or every remaining finding is a recorded decision. Set story
`status: revising` so `story next .` points at the next pass.

## Revision Workflow

1. Clarify the pass type unless the user already specified it. Each pass has a checklist in `references/pass-checklists.md` (what to run, read, check, and update); follow it from step 3 on, after the snapshot, because some checks write files:
   - **Continuity audit** - contradictions, stale references, timeline problems, missing backlinks, word-count drift
   - **Developmental revision** - structure, scene purpose, character motivation, pacing, stakes, arc progression
   - **Reverse outline** - what each chapter actually does, diffed against what the plot files say it should do
   - **Theme audit** - whether the ending engages the opening's value-question and early motifs pay off
   - **Pacing waveform** - tension per chapter and dead zones (`story pacing .`)
   - **Reveal economy** - every reveal earned by planted setup and spaced out (`story clues .`)
   - **Removability audit (darling-killing)** - scenes whose removal would change nothing downstream
   - **Length pass** - cut or expand to a target word count from a per-chapter and per-arc budget (`story progress .`, `story pacing .`; a custom `length` pass)
   - **Voice differentiation** - each speaker sounds like themselves (`story voices .`)
   - **Line edit** - clarity, voice, rhythm, dialogue, and sensory detail without changing plot facts (the `line-editing` skill)
   - **Copyedit** - style baseline and surface-detail consistency, not prose quality (the `line-editing` skill)
   - **Fact check** - real-world details against `research/` notes (the `research` skill)
   - **Proof/polish** - small wording, grammar, and formatting fixes on a built copy (the `line-editing` skill)
2. Snapshot the draft before any multi-chapter pass (see Draft Snapshots below), so the pass can be compared and undone.
3. Read the relevant context:
   - `story.md`
   - `chapters/_index.md`
   - The target chapter(s)
   - Previous and next chapters when present
   - Relevant character, location, system, and arc files referenced by the chapter frontmatter
   - Matching scene files in `scenes/`
   - `continuity/state.md`, open questions, and promises/payoffs
   - `plot/timeline.md` and active arc files for continuity-sensitive edits
   - The files the pass checklist lists, and the output of the checks it runs
4. Create a concise revision plan:
   - What will change
   - What must stay fixed for continuity
   - Which files may need updates beyond the chapter
   - Each scene, subplot, or passage the plan cuts, folds into another, or moves, named one by one

   Show the plan to the user and wait for their approval before editing. Cut, fold, or move only what they approve: a removability audit or a length pass proposes cuts, it does not make them. A single targeted edit the user has already spelled out ("revise chapter 3 so Nell hides the log") is its own approval, so state the plan in a line and go on.
5. Make targeted edits directly in markdown files, following the approved plan. Do not create project-local scripts to rewrite prose.
6. Update dependent metadata:
   - Chapter frontmatter `status` (`draft` -> `revised`, `revised` -> `final` only when appropriate)
   - Chapter `word-count` via CLI when available
   - `plot/timeline.md` if planned events or backstory changed (scene `date` and `time` say when drafted scenes happen)
   - `scenes/` records if POV, location, participants, or state changes moved
   - `continuity/state.md` when knowledge or object ownership changed
   - The one record that owns each setup the revision moves, adds, or cuts: a promise, clue, or question file (`status` and its chapter fields), or, for a small hint with no record, its arc `## Foreshadowing` row. Never record one setup in two places
   - Arc plot points if the revision changes which chapter hits them
   - Character or location files when state, relationship, or location references changed
7. Run maintenance:

```shell
story reindex .
story wordcount . --write
story check .
story doctor .
```

For structural or reveal passes, also run `story pacing .` and `story clues .`; after dialogue changes, `story voices .`. When working through named passes, finish with `story passes . --done <pass>`.

If `story.md` links other books through `follows` or `precedes`, also run `story series .` so the revision does not break canon shared with sequels or prequels. See the `series-continuity` skill.

`story continuity` deterministically checks death ordering (`died-in` vs later appearances, characters `deceased` with no `died-in` listed in any cast, and a character `status` progression to `deceased` followed by later appearances or learning, resolved in story order), status progressions that contradict `died-in` or `revived-in`, promise/question chapter ordering, unfired setups, POV/cast consistency, and `continuity/state.md` references. For intentional flashbacks, memories, or recordings of dead characters, list them under chapter or scene `mentions` instead of `characters`. A dead POV narrator keeps `pov` and is also listed in `mentions`; a resurrected character gets `revived-in: chapter-NN`; a death in an outline chapter is planned, not in force, so the character may keep `status: alive` and a later chapter may still list them until that chapter is drafted. Chapters dated on both sides compare deaths and `story knowledge` by story date, and a dual-timeline book's chapters take a `strand` so each timeline keeps its own clock and its own route check. `story knowledge` and `story context` mark a fact the character knows from a chapter the reader has not reached as `character-knowledge` with `do not reveal`: treat it as known, and do not state it. It also warns when `continuity/state.md` drifts from scene `state-changes` knowledge and artifact owners, from deaths, or from casts.

When any chapter has `choices`, the book branches and `story continuity` reads deaths, revivals, knowledge, and progressions along the paths of choices, while the promise, question, and clue ledgers and the clock still read chapter numbers. Revise it with the `interactive-fiction` skill as well: it covers `state-differs-by-path`, `unreachable-chapter`, rejoin prose, endings, and the hand checks for each path.

If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root.

## Draft Snapshots

Take a snapshot before a revision pass that touches more than one chapter, and name it after the draft it preserves (`draft-1`, `pre-beta-edit`).

- **Git projects:** work from the book's folder, the one that holds `story.md` (`cd` there first), because `-- .` below means the current folder. Make sure `.gitignore` lists `dist/` (`story init` writes one that does, but older or hand-made projects may lack it) so build output such as EPUB and DOCX files stays out of every snapshot and `story compare --ref` baseline; add the line if it is missing. Then run `git status --untracked-files=all -- .` and show the user what it lists. Look through it for private files (a `.env`, keys or credentials, scanned documents): unless the user says to commit one, add it to `.gitignore` first. Ask the user before committing anything; with approval, commit the book's folder only and tag it: `git add -A -- . && git commit -m "Draft 1 before developmental pass" -- . && git tag draft-1`. The `-- .` keeps files outside the book's folder out of the add and the commit, staged or not; when the book's folder is the repository root, that is the whole repository. If the status lists nothing, skip the add and the commit and run only the tag. If the user declines the commit, or it fails, never tag the last commit over an uncommitted tree: take a `story snapshot` as below instead, or stop. Never push, rewrite history, or delete tags without explicit approval.
- **Projects without git:** offer to run `git init` first. If the user declines, take a named snapshot: `story snapshot draft-1 --path .` copies the project's markdown to `.snapshots/draft-1/`, which every `story` command skips. It refuses a name already taken; ask before replacing one with `--force`. `story snapshot --list --path .` shows the snapshots there are. Never copy the project into a folder of its own by hand, where `story` commands would scan the copy.

After the pass, compare with the snapshot and report the result:

```shell
story compare . --ref draft-1
story compare . --snapshot draft-1
```

`story compare` lists each chapter's word change, added and removed chapters, and the share of paragraphs left unchanged, so the user can see how deep the pass went. Chapters are matched by id, but a chapter renumbered by `story move` whose paragraphs still mostly match is paired with its old id and shown as `(moved from chapter-NN)`. A chapter that was renumbered and also heavily rewritten (under half its paragraphs unchanged) shows as one removed and one added; compare those by content (read the old and new text side by side). It only reads git or the snapshot; it never commits, tags, or changes a snapshot. To see which passages survived the pass word for word, run `story similarity . --snapshot draft-1`.

If the user wants to abandon the pass and go back to the snapshot, use `story snapshot --restore draft-1 --path .`, never a hand copy. It deletes every project markdown file the snapshot lacks (a chapter added during the pass, say), and removes (`rmdir`) the folders that leaves empty, so run it with `--dry-run` first, show the user the files it would update, create, and delete and the folders it would remove, and restore only with their approval. Before changing anything it saves the project as `before-restore-draft-1-<n>` and prints that name; tell the user, since `story snapshot --restore before-restore-draft-1-<n>` undoes the restore. It never touches `dist/`, `.snapshots/`, other dot-folders, nested projects, or files that are not markdown, and it reindexes when done. Run `story validate .` afterwards. In a git project, ask before reaching for `git checkout` or `git reset` instead.

## Structural Edits

Chapter ids come from `number` (`chapter-07`), and scene ids embed the chapter id (`chapter-07-scene-02`), so moving a scene or renumbering a chapter changes ids. Use `story move`, never a hand rename: it renames the chapter and its scene files, updates `number`, the `# Chapter N:` heading, and scene `chapter`/`scene` fields, and rewrites every reference to the old id (clue and promise `planted`/`payoff`, question `introduced`/`resolved`, research `used-in`, `died-in`, `continuity/state.md` including `current-chapter`, links, and bare ids in `plot/timeline.md` and arc files).

1. Snapshot the draft first (see Draft Snapshots above)
2. Make the change:
   - **Insert a chapter:** move each later chapter up one, highest first, because `move` refuses a number that is taken: `story move chapter chapter-09 --number 10 --path .`, then `story move chapter chapter-08 --number 9 --path .`, and so on down to the gap. Then `story add chapter '<Title>' --number 8 --path .`
   - **Move a scene:** `story move scene chapter-03-scene-02 --chapter chapter-05 --path .` puts it at the next free number in chapter 5. Add `--scene <n>` to choose the position, or use `--scene` alone to reorder within its chapter. It adds the scene's location and characters to the new chapter; trim the old chapter's `locations` and `characters` by hand if the scene was the only reason for an entry
   - **Split a chapter:** `story split chapter-07 --at '<marker>' --path . --dry-run`, then without `--dry-run`. The marker is a scene break number (`--at 2` splits at the second break), a heading, or a unique line of the chapter text; `--title '<Title>'` names the new chapter (default `<title> (continued)`). The text before the marker stays in chapter 7, the rest becomes chapter 8, and the later chapters move up one. The new chapter takes the hook, POV, cast, locations, and status; the outline and `arcs-advanced` stay with chapter 7, so give chapter 8 its own beats and chapter 7 a new hook. Scene records follow their text by order. Read every `split-references` warning: a clue planted, a question introduced, a death, or a progression in the old chapter may now happen in the new one, and only you can tell, so repoint those to the new chapter. A `split-scenes` warning means the scene records did not line up with the text: fix them with `story move scene`. If `split` refuses because a file names the `chapter-NN` it would give a chapter (the last chapter it renumbers, or the new chapter when none follows; a payoff scheduled for a chapter not written yet, say), decide which chapter that reference means: point it at the chapter the message names to keep it with that text, or at the next id to keep it on the chapter after it, then run the split again
   - **Merge chapters:** `story merge chapter-07 chapter-08 --path . --dry-run`, then without `--dry-run`. It keeps chapter 7, appends chapter 8's prose after a scene break, adds its outline beats, notes, scenes, cast, and locations, points every reference to chapter 8 at chapter 7, takes chapter 8's hook, and moves the later chapters down one. Read every `merge-conflicts` warning: a field the two set differently (POV, date, time, or `numbered: false` on one of them) keeps chapter 7's value, and of two progressions of one field it keeps the later. Then smooth the join in the prose: the scene break may want to become a transition
   - **Branching books:** in a book with `choices`, `split` and `merge` work only on chapters with no choices, and `merge` only when no choice leads to the second chapter. They point every choice at the renumbered chapters and list each one, and a split gives the first half a `Continue` choice that leads to the rest: ask the user whether to reword it. To split or merge chapters with choices, insert or remove chapters with `story add chapter`, `story move`, and `story remove`, and rewrite the choices by hand (see the `interactive-fiction` skill)
3. `move`, `split`, and `merge` never edit prose. Reread for chapter numbers mentioned in the text ("back in Chapter 2") and for outline beats in the chapter bodies that no longer match
4. Run maintenance, then fix what it reports:

```shell
story reindex .
story wordcount . --write
story check .
```

`grep -rn "chapter-NN" .` finds references to an old id that the checks do not cover, such as ids in prose notes.

## Continuity Audit Checklist

Run `story continuity .` first to collect the deterministic findings, then check for what the CLI cannot judge:

- Character knowledge: no one acts on information they have not learned
- Character state: injuries, emotions, alliances, location, and status carry forward
- Timeline: time of day, travel time, sequence, and cause/effect stay coherent. `story timeline .` shows dated scenes in story order and marks flashbacks; check each marked scene is meant to be one. `story diagram timeline` prints the same order as a Mermaid timeline. `story continuity .` errors when a character moves between locations joined by `routes` faster than the route's `hours` allow
- Plot arcs: each changed scene still advances or intentionally pauses an arc
- Setups and payoffs: each promise, clue, and question record names the chapters where the prose now plants and pays it off, and each arc `## Foreshadowing` row (hints with no record) matches too; `story clues .` shows every clue's plant and payoff chapter
- Promises/questions: durable continuity records match what the chapter now reveals or withholds
- Scene state: every chapter scene has machine-readable POV, location, participants, arcs, and state-change notes
- World rules: magic, technology, politics, and geography stay consistent with worldbuilding files
- Deliberate findings: a dated flashback (`timestamp runs backward`) or a promise, question, or clue left open for a sequel (`is still planted` / `is still open` once `story.md` is `complete`) is correct as written. Do not change the data to silence it; add an entry to `continuity/exemptions.md` with the finding's `code` (the name in brackets at the end of a warning, or `code` in `story continuity . --json`) and its `file`, plus a `reason`, then run `story validate .` and rerun `story continuity .` and confirm it shows as `dismissed`. Prefer `code` plus `file` (or `chapter`) over copying the message into `pattern`: a reworded message then cannot stop the entry matching or make it match something new. Use `pattern` only to narrow further, such as which promise a `complete-with-open-promise` finding on `story.md` names. Never set `code` alone. Only genuine mistakes get fixed in the frontmatter
- References: chapter frontmatter lists every major character, location, and arc advanced in the prose. A chapter with no references is fine by design (a quiet two-hander advances nothing on paper) — only flag missing references, never empty ones.
- Registries: indexes, word counts, and links are current after edits

## Reporting

When the user asks for an audit rather than direct edits, return findings ordered by severity with file references and concrete fixes. When the user asks for revision, summarize the edited files, changed continuity facts, and maintenance results.

## Reference Files

- **`references/pass-checklists.md`** - One checklist per revision pass (run, read, check, update), mapped to the named passes that `story passes` tracks

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
