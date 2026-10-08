# Serial / Episodic Structure

Serial fiction (web serials, episodic novels, seasonal releases) needs
structure at **two layers**: the within-installment layer this reference
covers, and the book/season layer the `series-continuity` skill handles
(one project per book, canon carried across). Do not confuse them.

[`examples/the-left-luggage-office`](../../../examples/the-left-luggage-office/)
is the first three episodes of a serial with `season-goal`,
`episode-question`, per-episode `target-words`, a `hook` on each, and a
weekly release schedule (`release-every` and `release-start`).

## The release schedule

Record the cadence in `story.md` rather than in prose: `release-every`
(days between episodes, `7` for weekly, or months, `1 month` for monthly)
and `release-start` (the real-world `YYYY-MM-DD` day episode 1 goes out).
A monthly cadence releases on the same day each month, or on the month's
last day when the month is shorter: a serial that starts on the 31st goes
out on 28 or 29 February. Each chapter is an episode in reading order. A
chapter that moves off the cadence sets its own `release-date`. Release
dates are always Gregorian, even when the book has a story `calendar`. Run
`story progress .` or `story next .` to see the next episode due; both warn
(`release-undrafted`) when an episode due within three days, or already
past, has no prose or no chapter yet. Set `release-warn-days` in `story.md`
to change that window, such as `7` for a monthly serial that needs a week
to draft, or `0` to warn only from the release day. Draft that episode
first. When the last episode is written, set `status: complete` in
`story.md`: the cadence then stops at the last chapter, so the commands stop
scheduling episodes past it and stop warning about them.

## The season/volume goal

Every season (or volume, or series-arc) needs one **overarching goal**: the
thing the whole season is about. It should be statable in one sentence and
visible from the first installment:

- "Take the city back from the Hollow Men."
- "Find out who is killing the oath-bound."

The season goal gives installments their direction and the finale its
payoff. Record it in `story.md` (`season-goal:`) or in the hand-written
`## Story Structure` section of `plot/_index.md`. A serial without a season goal drifts — readers can feel
the absence by installment five.

## The per-episode dramatic question

Every installment must pose and **answer** one dramatic question — not the
season question, a smaller one:

- Installment 3: "Will Mara get the ledger out of the counting house?"
- Installment 7: "Who warned the Hollow Men?"

Rules:

- The question is posed early in the installment and answered by its end.
  An installment that only advances the season goal without resolving its
  own question feels like a fragment.
- The answer may raise a *new* question (chains are good), but it must not
  merely defer the original one.
- Record each installment's question in the chapter frontmatter
  (`episode-question:`) and its answer in the chapter notes.

## A reward in every installment

Serial readers pay per installment (in money or attention). Each one must
deliver something complete:

- A revelation, a reversal, a set piece, a relationship shift, a mystery
  answered — at least one **concrete payoff** per installment, even while
  larger threads stay open.
- The reward should be *proportional* to the installment's position: early
  installments reward with momentum and intrigue; late installments reward
  with payoff.
- Audit: list each installment's reward in one line. An installment with
  no reward is a candidate for merging with its neighbor.

## Recap discipline

Serial installments release apart in time; readers forget. But recaps that
read as recaps insult the reader:

- **Weave, don't dump:** re-establish essential facts through the
  installment's action (a character checks the wound from last time; a
  rival references the betrayal).
- **One-paragraph maximum** of explicit "previously" material, and only
  for facts the installment's plot *requires*. Everything else is the
  reader's problem — trust them.
- New-reader onboarding is a feature, not a bug: each installment should
  orient a new reader within its first page (who, where, what's at stake)
  without punishing returning readers. See
  `scene-craft/references/openings.md`.

## Arc-specific stakes (preventing endless escalation)

Serials die by escalation inflation: every installment bigger than the last
until the story is absurd. Instead, **vary the stake type** per arc:

- Personal stakes (a relationship), professional stakes (a position),
  physical stakes (safety), moral stakes (a principle) — rotate them.
- A quiet installment about a betrayal can land harder than a loud one
  about an explosion, *because* of the contrast. Plan the stake rotation
  in the season outline.

## Serial audit (per season)

- [ ] One-sentence season goal, visible from installment one.
- [ ] Release cadence recorded (`release-every`, `release-start`), and
      `story next .` shows no overdue episode.
- [ ] Every installment poses and answers its own dramatic question.
- [ ] Every installment delivers at least one concrete reward.
- [ ] Recaps are woven, not dumped; new readers can orient in one page.
- [ ] Stakes rotate in type; no three consecutive installments escalate
      the same stake.
- [ ] The season finale pays off the season goal *and* the longest-running
      installment questions.
