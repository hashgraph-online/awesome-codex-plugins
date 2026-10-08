# Path Continuity

Once any chapter has `choices`, `story continuity` reads "later" along the
paths of choices from the first chapter. This file covers what it follows,
what it still reads by chapter number, the branching findings, and the
checks left to you.

## What The Checker Follows By Path

A chapter is later than another when some path of choices leads from the
second to the first. So:

- **Deaths.** A character who dies on one branch may still appear on a
  sibling branch. At a rejoin, a death on any incoming branch counts: list
  the character in `characters` there and `story continuity` errors
  `posthumous-appearance`. Move them to `mentions`, or change the rejoin.
- **Revivals.** `revived-in` ends the death only when every path from the
  death passes through the revival chapter.
- **Knowledge.** `story knowledge <id> --at <chapter>` and `story context`
  show a fact once it is learned on some path to the chapter. At a rejoin
  that means a fact learned on only one incoming branch is listed as known.
  Use it in rejoin prose only when every incoming branch teaches it.
- **Progressions.** Character and location `progressions` apply in path
  order.
- **Dates.** Two chapters on one path dated on different days compare by
  date, so a flashback stays earlier. Sibling branches never compare.
- **Loops and unreachable chapters.** Two chapters that each lead to the
  other, and any chapter no path reaches, compare by date and then by
  number, as in a linear book.

## What Still Reads Chapter Numbers

These checks ignore the paths, so they can misread sibling branches:

- Promise, question, and clue ledgers (`planted`, `payoff`, `introduced`,
  `resolved`) and the Chekhov and open-question gaps
- The clock and route checks (`clock-backward`, `travel-too-fast`,
  `route-too-fast`)
- `story pacing` runs (consecutive `yes` outcomes, `resolution` hooks in a
  row)

`story series` and `story diagram` lifelines, and the second-death checks,
read every chapter in one order rather than path by path: the reading order
of the choices, so a chapter comes after the chapters that lead to it. A
death on one branch still counts at the end of the book.

A sibling ending dated earlier than the ending numbered before it reports
`clock-backward`. When the finding only reflects branch order, record it in
`continuity/exemptions.md` with the `code`, the `file`, and a `reason`
naming the branch, as the Gull Rock example does:

```yaml
exemptions:
  - code: clock-backward
    file: scenes/chapter-06-scene-01.md
    reason: "Chapter 6 is the other ending: readers reach it from chapter 4, not after chapter 5."
```

A promise planted on one branch and paid off on a sibling passes the
ledger check but is never paid off for any reader. Check each promise,
question, and clue against the paths by hand.

## The State Snapshot

`continuity/state.md` is one snapshot at `current-chapter`. It is checked
against the paths that lead there.

- Set `current-chapter` to the passage you last drafted. On a branch the
  snapshot describes that branch, and `story context` shows it only for
  passages a path leads to from there.
- An object change made before a split still holds on a branch that does
  not change it again.
- A character who learns the same fact on two branches takes one
  `knowledge-state` entry per branch, with the same `fact` id and each
  branch's chapter in `learned-in`:

  ```yaml
  knowledge-state:
    - character: ada-fenn
      fact: tobias-hurt
      knows: Tobias broke his ankle fetching oil
      learned-in: chapter-02
    - character: ada-fenn
      fact: tobias-hurt
      knows: Tobias broke his ankle fetching oil
      learned-in: chapter-03
  ```

### `state-differs-by-path`

```text
warning: continuity/state.md object-state for brass-key cannot match every path to chapter-04: scenes/chapter-02-scene-01.md sets mara-finn, scenes/chapter-03-scene-01.md sets jonas-reed; set brass-key owner again in a chapter the branches share, or check each path by hand [state-differs-by-path]
```

The branches that lead to `current-chapter` last set an artifact's owner or
location to different values, so no one `object-state` entry matches every
path. Fix it in the story, not the snapshot:

1. Decide where the object is at the rejoin on every path.
2. Write that into the rejoin chapter (or the last scene of each branch),
   with a scene `state-changes` entry that sets it.
3. Give the `object-state` entry `since:` the rejoin chapter. An entry
   whose `since` is after every branch's change settles the finding.

Setting `since` to the rejoin without step 2 silences the warning while
the prose still disagrees. If the object genuinely ends in different hands,
the branches should not rejoin there, or the difference belongs in a flag
in the built Twine or ink file; record the decision in
`continuity/exemptions.md` with a reason.

## Other Branching Findings

| Finding | From | Fix |
|---------|------|-----|
| `unreachable-chapter` | `story links`, Twee and ink builds | Add a choice that leads to the chapter, or remove it only with the user's approval after a snapshot and a `--dry-run` |
| A choice to a missing chapter | `story links` (error, except a `chapter-NN` with no file yet, which it allows as scheduled), builds refuse every one | Write the chapter, or point `to` at one that exists |
| Malformed `choices` (no `text`, link syntax in `text`, a `to` that is not kebab-case) | `story validate` | Fix the entry |
| Choices dropped by `story remove chapter` | `story remove` (warning) | Give each named chapter a new choice unless it is now a deliberate ending |

## Hand Checklist

The checker cannot judge these; check them before a draft is done:

- [ ] Every rejoin's prose is true on every incoming path
- [ ] Every fact a rejoin uses is learned on every incoming path
- [ ] Every path reaches an ending, and every loop has a choice out of it
- [ ] Every promise, question, and clue is planted and paid off on the
      same path
- [ ] Every flag in `notes/branch-map.md` is set on every path before it
      is read
- [ ] Every ending pays off the path that reaches it
