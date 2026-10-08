# Continuity and Analysis Checks

The rules each check command applies, and what to run it with. `SKILL.md` says when to run each command; read the matching section here before acting on its findings. These commands report; story decisions belong to the creative skills named in each section. `docs/continuity.md` explains the same checks for users, and `docs/cli-reference.md` lists every finding code.

## continuity

Run `story continuity .` after drafting or revising a chapter, and whenever the user asks about contradictions, dead characters appearing, unfired setups, or stale state.

### Deaths and revivals

It deterministically checks `died-in` ordering:

- It warns when a character `deceased` with no `died-in`, dead before the story, is in a cast.
- `revived-in` ends the dead window.
- A `died-in` outline chapter is a planned death, not in force, so the character may keep `status: alive` and a later cast is allowed until that chapter is drafted.
- A `pov` also in `mentions` is a posthumous narrator rather than an appearance.
- Chapters dated on both sides compare by story date, not number.
- A character `status` progression to `deceased` with no `died-in` counts as the death for later casts and learning, and a status progression that contradicts `died-in` or `revived-in` warns.

### Ledgers, casts, and state references

It also checks promise/question chapter ordering, Chekhov gaps, POV/cast consistency, `status: cut` characters still listed in a chapter or scene `pov`/`characters`, an arc's `characters`, or a relationship (warnings), and `continuity/state.md` references.

### `continuity/state.md` disagreements

It warns where `continuity/state.md` disagrees with:

- scene `state-changes`: a `character` + `knowledge` change with no `knowledge-state` entry learned by that chapter, or an artifact `owner`/`location` set by a later scene
- deaths: knowledge learned after dying, or `character-state` for a dead character
- casts: a `learned-in` chapter that does not list the learner, or a `character-state` location the `current-chapter` never visits

### Clue ledger

It reuses the promise-ordering machinery for the clue ledger (`continuity/clues/`): payoff before plant is an error (also when the planted chapter is a scheduled `chapter-NN` not written yet), and a completed story with planned or planted clues is an error.

### Chekhov gaps and unanswered questions

- The Chekhov warning requires `status: planted`: it fires as soon as a recorded payoff chapter has been drafted, or, with no payoff recorded, once three or more chapter files follow the plant (positions, not chapter numbers).
- An open question with no `resolved` chapter warns `question-unanswered` once twelve or more drafted chapters follow `introduced`, counted the same way; the finding stays a warning, and an open question is an error only once `story.md` is `complete`. Exempt one question meant to stay open with `code: question-unanswered` and its file, or set that code's `severity` to `off` to silence all of them.

### Planned and planted setups

- `story add clue --planted` (and `story add promise --planted`) records the chapter and sets `status: planted` when that chapter has a file, even an `outline` one; with `--planted` naming a chapter that has no file yet, or without `--planted`, the status is `planned`, and `--status` overrides either default. Pass `--status planned` while the planted chapter is only an outline.
- A promise or clue with `status: planned` and a `planted` chapter warns ("records planted chapter X but status is still planned") only once chapter X has prose, so `--status planned --planted chapter-NN` schedules a setup ahead.
- Both warnings read the named chapter's own `status`: an `outline` planted or payoff chapter does not count as drafted, even when later chapters are.
- A recorded payoff chapter that is not drafted yet suppresses the "no payoff yet" warning.
- `story links` accepts a scheduled `chapter-NN` that has no chapter file yet in `payoff`, in `planted` while the status is `planned` or `abandoned`, in an `open` or `abandoned` question's `introduced`, and in a research note's `used-in`, unless its number is 0 or belongs to an existing chapter under another id (`chapter-1` beside `chapter-01` is reported as missing); once the status is `planted`, `paid-off`, or `dropped` the planted chapter must exist, and once `paid-off` the payoff chapter must too. A question's `resolved` chapter must always exist. Cutting a planned thread needs only `status: abandoned`: leave its chapters in place. If a chapter with that number is added later, `story add chapter` and `story split` warn (`adopted-references`); clear the field then if the cut thread does not belong in that chapter. `story split` refuses to renumber an existing chapter onto a `chapter-NN` that any record names, or to give that id to its new chapter when a record other than an abandoned thread names it: point the record at the chapter it means first.

### Prop custody

It also checks prop custody: artifacts with `destroyed` or `lost` status must not be referenced after their destruction chapter.

- The destruction chapter is recorded in object-state `since: chapter-NN`; later scenes referencing the artifact in `state-changes` or `mentions` are errors.
- An entry with no `since` was destroyed or lost before the story, so any scene `state-changes` using it is an error while `mentions` stay allowed.
- A later entry for the same artifact with another status and a later `since` ends a loss.

### Clock and time plausibility

It checks clock/time plausibility when scenes or chapters carry `date: YYYY-MM-DD` / `time: HH:MM` frontmatter.

- `time` may be `dawn`, `morning`, `midday`, `afternoon`, `evening`, or `night`.
- Dated units are scenes, or a chapter with no scene records, in reading order, the same units `story timeline` shows.
- A unit that cannot fall after the latest moment reached warns as running backward and does not reset that moment, with named times read as the same spans as the route check and each chapter `strand` keeping its own clock.
- Scene `travel-hours: N` asserts the minimum time since that moment.
- A character, by scene `characters` or `pov` (the chapter's `pov` when the scene has none), in two dated scenes on the same chapter `strand` (chapters without one share a strand) at locations linked by location `routes`, with less story time between them than the fastest route, is an error, and so is a character at two different places at the same exact `HH:MM` on one strand whether or not routes join them; a sighting in another strand is not the other end of a journey.
- The route check reads scene `date`, `time`, and `location` only, not chapter dates; a named time is a span such as `morning` 05:00-11:59, an untimed scene spans its whole day, and only journeys impossible on every reading are reported.
- Without dates, only malformed dates or times and `travel-hours` on an undated scene are reported.

### Exemptions

Intentional exceptions go in `continuity/exemptions.md` (frontmatter `type: exemption-log`, entries with a `reason` and the finding's `code` plus its `file` or `chapter`, as `--json` diagnostics give them; `pattern` matches message text and still works); exempted findings are reported as dismissed, not errors.

## Branching books

Once any chapter has `choices`, `story continuity` (and `story check`, which reports the same findings), `story knowledge`, and `story context` read "later" along the paths of choices from the first chapter. Read this before acting on their findings in a branching book. Writing rejoins, recording a fact learned on two branches, and fixing `state-differs-by-path` are covered by the `interactive-fiction` skill's `references/path-continuity.md`.

### What follows the paths

- **Deaths and revivals.** A death on one branch is not a posthumous appearance on a sibling branch. At a rejoin, a death on any incoming branch counts, so listing the character in that chapter's `characters` or `pov` is a `posthumous-appearance` error. `revived-in` ends the death only when every path from the death passes through the revival chapter. Learning after death and status progressions use the same rule.
- **Dates.** Two chapters on one path dated on different days compare by date, so a flashback reached later stays earlier. Dates in a `story.md` custom `calendar` compare the same way. Chapters on sibling branches never compare.
- **Knowledge.** `story knowledge <id> --at <chapter>` and `story context` list a fact once it is learned on some path to the chapter. At a rejoin, a fact learned on only one incoming branch is listed as known, so check that every incoming branch teaches it before the rejoin prose uses it. One `knowledge-state` entry per branch for the same `fact` is not a `state-duplicate-fact` error.
- **Context.** `story context` takes previous scenes, open promises, clues, and questions, and progressions only from chapters on a path to the target. At a rejoin that is every incoming branch. It shows the `continuity/state.md` character state only when `current-chapter` comes before the target on some path, whatever the chapter numbers; when `current-chapter` is on a sibling branch it prints a line saying the snapshot is left out.
- **Prop custody.** A destroyed or lost artifact is gone only on paths after its `since` chapter.
- **`continuity/state.md`.** It is checked against the chapters on a path to `current-chapter`. When those branches last set an artifact's `owner` or `location` differently, it warns `state-differs-by-path`.
- **Loops and unreachable chapters.** Two chapters that each lead to the other, and any chapter no path reaches (`story links` warns `unreachable-chapter`), compare by date and then by number, as in a linear book.

### What still goes by chapter number

These read the chapters in number order, so sibling branches can produce findings no reader meets:

- the promise, clue, and question ledgers: payoff before plant, and the chapter counts behind the Chekhov and `question-unanswered` warnings. A setup planted on one branch and paid off on a sibling passes, though no reader sees both, so check each one against the paths by hand.
- the clock and route checks (`clock-backward`, `travel-too-fast`, `route-too-fast`, `route-same-time`), which compare every dated scene in a `strand`, whichever branch it is on
- `story timeline`, which marks a sibling ending dated before the one numbered ahead of it as told "after later events"
- `story grid`, whose columns are every chapter side by side in number order, whichever path reaches each
- `story pacing` runs, `story next`, and the `progression-out-of-order` list order

`story series` and `story diagram` lifelines, and the second-death checks that read them (`revival-status-mismatch`, `deceased-without-died-in`), read every chapter in one order, not path by path: the reading order of the choices, so a chapter comes after the chapters that lead to it, with dated chapters by date. A death on one branch still counts at the end of the book.

### Sibling-ending clock warnings

Two endings reached from the same chapter are alternatives, but the clock reads the higher-numbered one after the other. If its scene is dated earlier, `clock-backward` reports it. When that finding only reflects branch order, keep the dates and exempt the finding by `code` and `file`, with a `reason` naming the branch:

```yaml
exemptions:
  - code: clock-backward
    file: scenes/chapter-06-scene-01.md
    reason: "Chapter 6 is the other ending: readers reach it from chapter 4, not after chapter 5."
```

`examples/the-gull-rock-light` does this, and `story continuity` reports it as `dismissed: scenes/chapter-06-scene-01.md timestamp runs backward (exemption: ...)`. Exempt only the branch-order finding. A `clock-backward` warning between two chapters on one path is a real clock problem: fix the dates or times.

## clues

Run `story clues .` for mysteries and any story with a clue ledger. It prints a clue-by-chapter matrix (`P` planted, `R` payoff, `x` both, `.` none; `~` after a clue name marks a red herring) and warns about:

- a payoff with no plant
- a late plant (same chapter as the payoff, or the one before)
- a clue with no `characters`
- three or more genuine live clues (not red herrings) with none `significance-delayed`
- a `red-herring: true` clue with no `payoff`

See the `genre-craft` skill.

## add clue

Run it when the user plants a new clue. `story add clue 'Name' --planted chapter-02 --payoff chapter-05` creates the clue ledger entity in `continuity/clues/` with `status: planted` (`planned` when `--planted` is omitted or names a chapter with no file yet; pass `--status planned` if the chapter has a file but the clue is not on the page yet). Omit `--payoff` when the payoff is not yet known, and pass `--red-herring` for a clue meant to mislead.

## pacing

Run `story pacing .` when the user asks about pacing, sagging middles, or chapter endings, and after drafting or restructuring chapters. Per chapter it shows words, scene and sequel counts, scene `outcome`s (`yes`, `no`, `yes-but`, `no-and`), and the chapter `hook` (`cliffhanger`, `question`, `revelation`, `reversal`, `decision`, `emotional`, `resolution`). It warns about:

- three or more consecutive `yes` outcomes
- four or more scene units with no sequel
- chapter length outliers (over 2x or under 0.5x the median once three chapters have prose)
- three or more consecutive chapters ending on `resolution`
- drafted chapters with no `hook`

See the `plot-structure` and `scene-craft` skills.

## voices

Run `story voices .` when dialogue voices may blur or during a line pass.

- It attributes a quoted line (straight `"..."`, curly `“...”`, or British `‘...’`) when the narration names the speaker next to a speech verb (`"...," Mara said`, `said Mara`, `Mara asked`, aliases included). A name before the verb wins over a name after it: in `"...," Sera told Kael` the line is Sera's, and `said Kael` gives it to Kael. With no speech-verb tag, a paragraph whose narration names exactly one character (an action beat) gives the line to that character.
- Names and aliases match case-sensitively as proper nouns, and titles are skipped for the given name (`Lord Maren` also matches `Maren`).
- Pronoun tags (`she said`, `said he`) are never attributed, and a paragraph with one is left unattributed even when its narration names another character. Only a pronoun and verb right after a closing quote or right before an opening one count as a tag; `She said nothing more` elsewhere is narration and does not block an action beat.
- In close third person the POV character is often under-counted; when that matters, name the tags in a sample chapter and rerun. Unattributed dialogue is not counted, so a low line count may mean few named tags rather than few lines.
- Per character it reports lines, words, mean sentence length, contraction, question, and exclamation rates, and signature words used more by them than by others.
- It warns when a character says one of their `voice-avoid` words, when two characters with five or more lines each have close fingerprints ("X and Y may sound alike: similar sentence length, contractions, questions, and exclamations"), and when a character with five or more lines never says a `voice-words` entry.

See the `voice-style` and `line-editing` skills.

## prose

Run `story prose .` when the user asks for a prose check or before sharing a draft.

- Per chapter it counts sentence length and spread, filter words and -ly adverbs per 1,000 narration words, plain and said-bookism dialogue tags, echoed words, watch words, and avoided spellings from `style-sheet.md` (`dialect`, `preferred`, `watch-words`, `allow-words`).
- Across the manuscript it lists repeated 4-word phrases and similar character first names.
- Findings are advisory warnings. The command exits 0 unless `story.md` `severity` promotes one, or the command line is wrong, such as `--baseline` with no `samples` (exit 2).
- `--max-filter-words <n>` (default 10), `--max-adverbs <n>` (default 12), and `--max-bookisms <n>` (default 2) change the warning thresholds.

See the `voice-style` skill for acting on them.

## mentions

Run `story mentions <kind> <id> --path '<project>'` to list every place the chapter prose names a character, location, faction, artifact, system, or glossary term, and before `story remove`, which never changes prose, or `story rename` without `--prose`.

- It looks for the `name`, `aliases`, a character's given name (not an initial such as the `J` of `J. R. Dunn`), and each without leading titles or articles (`Hollow` for `The Hollow`). Names match as written and as whole words, so `Rose` is not found in "a rose"; possessives count. Outlines, HTML comments, and code fences are skipped.
- `story continuity` warns `named-not-listed` when a drafted chapter's prose names a character that its `pov`, `characters`, and `mentions` leave out. Add them to `characters` if they are on the page, or `mentions` if they are only talked about. A one-word name that opens a sentence is not counted when the chapter also uses it as a plain word.
- `story mentions` with no entity also warns `mention-not-named` for a character or artifact in `mentions` that the prose never names. A chapter that refers to someone only by relationship ("her father") triggers it, so read the chapter before acting: add the name the chapter uses to the entity's `aliases`, drop a stale mention, or exempt it.

## names

Run `story names '<name>' ...` before naming a character, place, faction, artifact, system, or glossary term. It checks candidates against every existing name and alias.

- A candidate's given name (first word that is not a title or article such as `the`, `lord`, or `captain`) is compared with each character's given name, and everything else as a whole name; an exact match with either is a clash, an error (exit 1).
- Look-alikes (the same first four letters, or the same initial within edit distance 1, or 2 when both words have five letters or more) and a given name sharing an initial with a protagonist, antagonist, deuteragonist, or narrator are warnings.
- Multi-word names are only checked for exact clashes, so pass a multi-word name's distinctive words separately.
- Pass `--path <project>` when not in the project root.

## timeline

Run `story timeline .` when the user asks what happens when, how flashbacks sit against the main line, whose POV dominates, or where a character drops out. It orders dated scenes (and chapters without scene records) by `date` and `time`, marks entries told after later events, lists undated scenes in reading order, totals chapters and words per POV, and reports each character's chapter presence, longest absence, and absence from the final chapters. It is read-only; `continuity` owns clock errors.

## knowledge

Run `story knowledge <character-id> --at <chapter-id>` when the user asks what a character knew at a given chapter. It lists knowledge-state entries the character knows there in story time (by date when both chapters are dated, otherwise by chapter number), plus entries without `learned-in`. Each line is `reader-knowledge` (already on the page, or pre-existing) or `character-knowledge` with `do not reveal` (known from a flashback the reader has not reached). `story context` uses the same rule and the same marks.

## context

Run `story context <chapter-or-scene-id> [--budget <tokens>] [--scenes <n>]` before drafting a chapter or scene.

- It prints, as markdown and in priority order until the estimated budget runs out, the target's outline and cast, the `story.md` essentials and `style-sheet.md` rules, the POV character's knowledge and state at that point, cards for the characters on the page and the locations, with their progressions applied at the target, open promises, clues, and questions, and summaries of the previous `--scenes` scenes (default 5).
- The budget defaults to 6000 tokens, estimated at 4 per 3 words in spaced text, 2 per 3 Han or katakana characters, 1 per 2 hiragana, and 1 per Thai, Lao, Khmer, or Burmese word.
- POV knowledge follows the same rule as `knowledge`, including a `character-knowledge` line that must not be revealed. Other material from later chapters is left out, progressions included.
- For a scene, a fact learned in that chapter is included only when an earlier scene's `state-changes` records it for the POV character.
- Items left out for the budget are listed with the file to read instead.

## passes

`story passes .` tracks named revision passes in `story.md` `revision-passes` (`{pass, status}`, status `pending`, `in-progress`, or `done`).

- `--init` writes the default ladder (`structure`, `character`, `theme`, `continuity`, `pacing`, `line`, `copyedit`, `proof`) and keeps existing entries.
- `--start <pass>` and `--done <pass>` update one.
- With no flag it prints the checklist and the checks each default pass runs.
- When the story `status` is `revising`, `next` recommends the next unfinished pass.

See the `revision-continuity` skill.

## compare

Run `story compare . --ref <git-ref>` or `story compare . --against '<project-path>'` after a revision pass, or when the user asks what changed since a draft. It needs exactly one of `--ref`, `--against`, or `--snapshot`.

- `--ref` reads chapters at a git branch, tag, or commit with `git show` (it never writes to the repository), and `--against` reads another copy of the project.
- It reports per-chapter word changes, added and removed chapters, and the share of paragraphs unchanged.
- With `--anchor <label>` (repeatable) it instead maps review-copy paragraph labels from that draft to the current text, one line per label: `ch01-p20 -> ch01-p21 (text unchanged)`, `(edited, NN% similar)`, `not found in the current text ("first words…")`, or `no such label`. Use it to resolve reader notes from an older build.

See Draft Snapshots in the `revision-continuity` skill for taking the snapshot.

## similarity

Run `story similarity . --against '<source>'` when the user asks whether a passage echoes another text too closely: their earlier books, a previous draft, or a source they worked from.

- `--against` takes a file, a folder (another story project's chapters, or every `.md`, `.markdown`, and `.txt` file in it), or a git ref.
- It reports each run of `--min-words` (default 8) or more shared words, compared lowercased without punctuation, as a `similarity-shared-passage` warning with the chapter's review-copy label, the reference's location, and the shared words, then per-chapter and total shares.
- It is advisory and exits 0. Shared text is not proof of copying, so report what it found and where, never a verdict.

See the `editorial-review` skill.

## series

Run `story series .` when `story.md` has `follows` or `precedes` links to other books.

`story series [path]` finds every book reachable through `follows` and `precedes`, then orders them by chronology. At each step, among the books whose earlier books are already listed, the lowest `book-number` goes next, then title, then folder path. It only follows links between sibling book folders. It lists shared canon and reports:

- **Errors**
  - A linked path that is not a story project
  - Books that declare different `series` ids
  - Two books that share a `book-number`, or a `book-number` that is not a number 0 or more
  - A chronology cycle
  - A character who is dead at the end of an earlier book (by `died-in`, a status progression to `deceased`, or `status: deceased`) but not `deceased` in a later one
  - A later book whose chapter or scene lists that character as `pov` or under `characters`, before a status progression in that book brings them back. Move flashbacks, memories, and ghosts to `mentions`. A ghost narrator may stay the `pov` when also listed in `mentions`.
  - A later book where a character learns a `fact` (an entry with `learned-in`) that the same character already knows in an earlier book. In a prequel, the usual fix is to remove the knowledge from the prequel, or to change which book the discovery happens in.
  - A later book where a character who died in an earlier book learns something (a `knowledge-state` entry with `learned-in`) before being brought back
  - A later book's scene whose `state-changes` target an artifact `destroyed` in an earlier book
- **Warnings**
  - A shared entity whose `name` (or glossary `term`) or `pronunciation` differs from the most recent earlier book
  - Linked books that set different `series-title` values
  - An artifact that is `destroyed` in an earlier book but has a different status in a later one
  - Linked books that set no `series` id while the others share one (`Linked books <titles> set no series id; add series: <id>`); add the id to each named book

See the `series-continuity` skill. `docs/series.md` gives the fix for each finding.
