# Revision Pass Checklists

One section per revision pass. Each section says what the pass is for, which
checks to run, what to read, what to look for, and which files to update. Pick
the pass in step 1 of the Revision Workflow in `SKILL.md` and take the
snapshot in step 2 before running anything here: some checks write files,
such as `story wordcount . --write`. Then follow the pass's section through
the reading, planning, editing, and maintenance steps.

The named passes that `story passes .` tracks in `story.md`
`revision-passes` map onto these checklists:

| Ladder pass | Checklists |
|-------------|------------|
| `structure` | [Reverse outline](#reverse-outline), [Pacing waveform](#pacing-waveform), [Removability audit](#removability-audit-darling-killing) |
| `character` | [Developmental revision](#developmental-revision), [Voice differentiation](#voice-differentiation) |
| `theme` | [Theme audit](#theme-audit) |
| `continuity` | [Continuity audit](#continuity-audit), [Reveal economy](#reveal-economy), [Fact check](#fact-check) |
| `pacing` | [Pacing waveform](#pacing-waveform) |
| `line` | [Line edit](#line-edit) |
| `copyedit` | [Copyedit](#copyedit) |
| `proof` | [Proof/polish](#proofpolish) |
| `length` (custom) | [Length pass](#length-pass) |

## Adding a pass

Give a new pass its own `##` section with the same headings, in this order,
and add it to the table above. Leave out a heading that does not apply.

```markdown
## {Pass name}

{One or two sentences: what the pass finds and why it matters.}

- **Run:** {story commands, with what to look for in their output}
- **Read:** {project files}
- **Check:** {what to judge by reading}
- **Update:** {files the pass may change}
- **See also:** {skill or reference that owns the deep version}
```

A custom ladder entry (`story passes . --start fact-check`) needs no section
here unless it brings a procedure of its own.

## Continuity audit

Find contradictions, stale references, timeline problems, missing
backlinks, or word-count drift.

- **Run:** `story reindex .`, `story wordcount . --write`, and
  `story check .`: the first two correct registry and word-count drift,
  and `check` reports the deterministic continuity findings, missing
  backlinks, and validation errors.
- **Check:** what the CLI cannot judge, using the Continuity Audit
  Checklist in `SKILL.md`.
- **Update:** the chapter, and every dependent record listed in step 6 of
  the Revision Workflow.

## Developmental revision

Improve structure, scene purpose, character motivation, pacing, stakes, and
arc progression.

- **Run:** `story knowledge <id> --at <chapter>` for what a character knows
  when they act, and `story diagram relationships` for how relationships
  stand.
- **Read:** the chapters, the arc files they advance, and the character
  files of the main cast.
- **Check:** each scene has a purpose, each character's motivation explains
  what they do, stakes rise, and each arc progresses.
- **Update:** chapters, scenes, arc plot points, and character files whose
  arc or state changed.

## Reverse outline

Extract what each chapter actually does in one line per chapter, without
looking at the outline or arc files, then diff that against what the plot
files say it should do. Reorder, merge, split, or cut where they disagree.

- **Read:** every chapter in `chapters/`, `plot/timeline.md`, active arc
  files.
- **Update:** `plot/timeline.md` and arc plot-point tables when chapters
  move, merge, or split. Make the moves with `story move`, `story split`,
  and `story merge` (see Structural Edits in `SKILL.md`), which rebuild
  `chapters/_index.md`; never edit its rows.

## Theme audit

Check whether the ending engages the opening's value-question and whether
the theme is dramatized through consequence rather than commentary. Verify
every motif introduced early is paid off by the end.

- **Run:** `story report .`.
- **Read:** `story.md` premise and themes, the opening and closing chapters,
  theme-tracked arcs in `plot/_index.md`.
- **Update:** `story.md` premise if the draft argues a different idea, arc
  `themes` tags.
- **See also:** the `theme-craft` skill for the deep pass.

## Pacing waveform

Map tension per chapter to find dead zones: chapters that neither raise nor
vary the tension level. Two peaks back-to-back dilute each other; a flat
middle means escalation is missing.

- **Run:** `story pacing .` for the per-chapter dashboard (words, scene and
  sequel counts, scene `outcome`s, chapter `hook`) and its warnings:
  - three or more consecutive `yes` outcomes (no pressure)
  - four or more scene units without a sequel (no breath)
  - chapter length outliers
  - three or more chapters in a row ending on `resolution`
  - drafted chapters with no `hook`

  Run `story timeline .` for POV balance and characters who vanish for long
  stretches.
- **Read:** the chapters, `scenes/` state-changes, arc climax points.
- **Update:** chapter or scene order, or add escalation where the map goes
  flat.

## Reveal economy

Check that every reveal is earned by planted setup and that reveals are
spaced rather than dumped in clusters. Unplanted twists and reveal dumps
both read as cheap.

- **Run:** `story clues .` for the clue-by-chapter matrix and its fair-play
  warnings (late plants, unplanted payoffs, clues nobody can notice,
  undebunked red herrings). `story diagram clues` draws the plant-to-reveal
  flow.
- **Read:** `continuity/promises/`, `continuity/clues/`,
  `continuity/questions/`, arc foreshadowing tables (hints with no
  record), `knowledge-state` in `continuity/state.md`.
- **Update:** the `status` and chapter fields of the one record that owns
  each setup (a promise, clue, or question file), or the arc foreshadowing
  row for a hint with no record.

## Removability audit (darling-killing)

Find scenes whose removal would change nothing downstream: no state
changes, no causality, no payoff. For each one, propose a treatment: wire
it in (give it consequence), fold it into an adjacent scene, or cut it.
Show the user the list and let them decide; fold or cut only the scenes
they approve. Then record each decision so nobody re-litigates it.

- **Read:** `scenes/` state-changes, `continuity/state.md`,
  `continuity/promises/`.
- **Update:** scene `state-changes`, promise/question status,
  `plot/timeline.md`.

## Length pass

Cut an overlong draft (140,000 words down to 100,000) or expand a thin one
to a target length. Set a budget per chapter and arc before touching prose:
trimming every chapter by the same share flattens the book, while a budget
takes words from the parts that are slack and keeps them where the story
turns. Run it after `structure` and before `line`, so no sentence is
polished and then cut. Track it as a custom pass with
`story passes . --start length`.

- **Run:**
  1. `story progress .` for the total against `story.md` `target-words`
     (`target-characters` in a book counted in characters). With no
     target, agree one with the user and set it first. `story validate .`
     warns when the target sits outside the `form`'s usual range; confirm
     the target with the user rather than changing the form to silence it.
  2. `story pacing .` for each chapter's length, scene and sequel counts,
     and outcomes, plus the median chapter and its `pacing-long-chapter`
     and `pacing-short-chapter` outliers.
  3. Set the budget. Start each chapter at its count times target over
     total (100,000 / 140,000 keeps about 71% of each), then move words
     between chapters: protect the opening, act turns, midpoint, climax,
     and chapters that pay off a promise or clue; take more from long
     outliers, runs of sequels, and chapters whose scenes advance no arc.
     Expanding, give words to short outliers, scene runs with no sequel,
     and arcs with missing plot points. Keep the budgets summing to the
     book target, as whole numbers, and write nothing yet.
  4. Budget each arc: add up the counts of the chapters whose
     `arcs-advanced` lists it and compare its share of the book with its
     weight in `plot/_index.md`. A subplot that takes a quarter of the book
     for one late payoff is the first cut; a main arc squeezed into a few
     chapters is where an expansion goes.
  5. Put the chapter budgets and the cuts they imply in the revision plan
     (step 4 of the Revision Workflow in `SKILL.md`). Once the user
     approves it, write each budget to the chapter's `target-words`
     (`target-characters`): `story progress .` then lists every chapter
     against its budget (`chapter-01: 101 of 70 words (144%)`), and
     `story context <chapter>` shows it when the chapter is redrafted.
  6. After each batch of edits, run `story reindex .`,
     `story wordcount . --write`, and `story check .`, then
     `story progress .` again, until the total is within the tolerance
     agreed with the user (say 2%).
- **Read:** `story.md` (`target-words`, `form`), `chapters/_index.md`,
  `plot/_index.md` and the arc files, `scenes/` state-changes,
  `continuity/promises/`, `continuity/questions/`, `continuity/clues/`.
- **Check:** agree the cuts with the user before making any. Show them the
  budget and name each subplot, scene, or chapter you propose to cut or
  merge, and cut only what they approve. Cut biggest first: whole subplots and scenes (the
  [removability audit](#removability-audit-darling-killing)), then merge
  scenes or chapters that do the same job, then compress (summarise
  transit, repeated sequels, backstory, and description), and trim
  sentences last with the `line-editing` skill. Before cutting a scene,
  check it does not plant or pay off a clue or promise, teach a character
  something they later act on, or carry a state change; move what it
  carries to a scene that stays. Expand by adding scenes or sequels that
  change something, not by padding existing ones.
- **Update:** chapters, scenes (merge and remove with `story merge`,
  `story move`, and `story remove`, see Structural Edits in `SKILL.md`), chapter
  `target-words`, promise, question, and clue chapters, arc plot points,
  `plot/timeline.md`, and `continuity/state.md`. When the pass is done,
  ask whether to keep the chapter budgets as targets or remove them.
- **See also:** the `plot-structure` skill for arc weight, `scene-craft`
  for new scenes, and `line-editing` for sentence-level trims.

## Voice differentiation

Check that each speaker sounds like themselves.

- **Run:** `story voices .` for per-character dialogue fingerprints. It
  warns when two characters' fingerprints are near-identical, when a
  character says a word from their `voice-avoid` list, and when a
  `voice-words` entry never appears.
- **Update:** dialogue in chapters, or the character's
  `voice-words`/`voice-avoid` when the draft has found a better voice.

## Line edit

Improve clarity, voice, rhythm, dialogue, and sensory specificity without
changing plot facts.

- **Run:** `story prose .` to find filter words, adverb clusters,
  said-bookisms, echoes, uniform rhythm, and repeated phrases worth
  rereading.
- **Read:** `style-sheet.md` for the recorded voice.
- **See also:** the `line-editing` skill for a full prose-quality pass.

## Copyedit

Distinct from proof/polish: enforce a style baseline (hyphenation,
capitalization, naming, numbers) and continuity of surface detail (hair
color, room layouts, name spellings). This pass is mechanical consistency,
not prose quality; prose quality belongs to the line edit.

- **Run:** `story prose .` and fix every avoided spelling it reports.
- **Read:** `style-sheet.md` (create it with the `voice-style` skill if
  missing), `glossary/`, character and location files.
- **Update:** chapters, `style-sheet.md` when a new convention is settled,
  `glossary/`, character files where details drifted.
- **See also:** the `line-editing` skill for the full copyedit procedure.

## Fact check

Verify real-world details the chapter relies on.

- **Read:** `research/` notes whose `used-in` lists the chapter.
- **Update:** research notes and their status, and the chapter where it
  contradicts verified findings.
- **See also:** the `research` skill.

## Proof/polish

Fix small wording, grammar, repetition, and formatting issues.

- **Run:** proof a built copy, not the source: `story build . --format
  print` or `--format html`.
- **See also:** the `line-editing` skill.
