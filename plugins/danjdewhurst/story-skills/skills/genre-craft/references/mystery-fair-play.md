# Mystery: Fair Play and the Clue Ledger

The fair-play doctrine is the genre's contract with the reader: the reader
must have every clue the detective has, in time to solve the mystery
themselves. A mystery that withholds essentials is not clever — it is
cheating.

## Fair-play rules

- **The reader gets every clue.** Every fact the detective uses to solve the
  case must appear on the page before the solution, early enough to matter.
- **The culprit is introduced early** — conventionally within the first
  third. A culprit who appears only at the reveal is a stranger, not a
  suspect.
- **No withheld essentials.** The detective may not know something the
  reader doesn't (no secret evidence revealed at the gather-suspects scene).
  The detective may *misinterpret* — that is the game — but the facts must
  be shared.
- **The solution must be the best explanation of the planted clues**, not
  merely a consistent one. If three solutions fit the clues, the planting
  was too thin.

## Clue-planting techniques

- **Hidden in plain sight:** the clue appears as set dressing or a throwaway
  detail. The reader sees it; only the detective's context makes it a clue.
- **Camouflaged:** the clue is embedded in a longer list or a busy scene —
  one wrong alibi among five correct ones, one inconsistent detail in a
  full witness statement.
- **Misinterpreted:** the clue is correctly observed but wrongly explained,
  by the detective or by a witness the reader trusts. The reveal reframes it.
- **Absence as clue:** the dog that didn't bark — something that *should*
  be present and isn't. Plant the expectation early so the absence registers.

## Red-herring discipline

- Every red herring must be **plausible** (a reasonable reader could suspect
  this person), **scene-fitting** (it belongs in the scenes it appears in —
  never inserted solely to mislead), and **resolved, not abandoned**.
- A resolved red herring gets its own mini-payoff: the suspect is cleared
  *for a reason that teaches the reader something true* about the case.
- Mark herrings with `red-herring: true` in the clue's frontmatter, and use
  `payoff` for the chapter that debunks it. `story clues` warns about a red
  herring with no `payoff`: an undebunked herring is a broken promise. Note
  how it is cleared in the clue's prose. Set `status: planted` when the
  herring is on the page, and `status: paid-off` or `abandoned` when it is
  resolved.

## The gather-suspects reveal

The classic reveal structure: assemble the suspects, walk through the
evidence, eliminate each in turn, name the culprit. Requirements:

- Every elimination must use **planted** clues (check the ledger).
- The culprit's motive, means, and opportunity must each trace to a planted
  clue — three separate ledger entries minimum.
- The scene works best when the detective is *wrong about one thing* on the
  way to being right — it keeps the reveal from feeling like a lecture.

## The clue ledger

Maintain `continuity/clues/` with one file per clue (kebab-case ids). The
CLI creates them with `story add clue`:

```shell
story add clue 'The silver locket' --planted chapter-02 --payoff chapter-05
```

Omit `--payoff` when the payoff is not yet known. `--planted` records the
chapter and sets `status: planted` when that chapter has a file, even an
outline; with a chapter that has no file yet, or without `--planted`, the
status is `planned`. Pass `--status planned` if the chapter has a file but
the clue is not on the page yet. The generated frontmatter:

```yaml
---
title: The silver locket
status: planted
planted: chapter-02
payoff: chapter-05
significance-delayed: false
characters: []
arcs: []
---
```

Set `significance-delayed: true` only when the reader sees the clue before
understanding it. Set `red-herring: true` when the clue misleads (pass
`--red-herring` on `story add clue`, or edit the file later); its `payoff`
is the chapter that clears it. Pass `--significance-delayed`,
`--character`, and `--arc` on `story add clue` when those values are
known. List characters and arcs as block entries, the
way the CLI writes them. `characters` names who can notice the clue (the
detective, the witness); a clue nobody can notice cannot be played fair.

- `planted` must precede `payoff`. `story continuity` errors when payoff
  comes before plant. The Chekhov warning fires only when `status` is
  `planted`: as soon as a recorded `payoff` chapter is drafted, or, with no
  payoff recorded, once the plant is three or more chapters back. A clue kept
  at `status: planned` with a `planted` chapter records where it will go;
  once that chapter has prose, `story continuity` warns until the status is
  `planted`. A completed story that still has a `planned` or `planted`
  clue is an error.
- A clue with `significance-delayed: true` is fair play *only if* the clue
  itself was visible; delayed significance is the game, hidden clues are
  the cheat.
- After adding or editing clues, run `story reindex .`,
  `story wordcount . --write`, and `story check .`, then `story clues .`

## The fair-play matrix

`story clues .` prints the ledger as a grid: clues as rows, chapters as
columns. `P` marks the chapter a clue is planted, `R` its payoff or reveal,
`x` both, `.` neither; a red herring has `~` after its clue name. Read down a column to see
what the reader holds at each chapter, and along a row to see how long a
clue waits. It warns about:

- A clue with a payoff but no plant (the reveal uses an unplanted fact)
- A late plant: planted in the same chapter as its payoff, or the chapter
  immediately before, so the reader cannot play fair
- A clue with no `characters` (nobody in the story can notice it)
- A story with three or more genuine live clues (not red herrings; status
  `planned`, `planted`, or `paid-off`) and none `significance-delayed`
  (every clue is understood on sight, so there is no puzzle)
- A red herring with no `payoff` (never debunked)

`story diagram clues` prints a Mermaid flow of each clue from plant to
reveal by chapter, useful for spotting reveal clusters where the solution
arrives in a dump. Save it with `--out dist/clues.mmd` when the user wants a file;
keep generated diagrams out of the entity folders.

Run `story clues .` when planning the ledger, after each drafted chapter
that plants or pays off a clue, and in the revision audit.

## Mystery audit (revision)

- [ ] `story clues .` reports no late plants, unplanted payoffs, or
      undebunked red herrings (or each remaining one is a recorded decision).

- [ ] Every clue the solution uses is planted before the reveal.
- [ ] The culprit appears in the first third.
- [ ] Every red herring is cleared with a reason.
- [ ] No essential fact first appears in the reveal scene.
- [ ] The detective's wrong turns use misinterpretation, not missing facts.
