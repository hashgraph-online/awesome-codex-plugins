# Drafting Cadence and Sprints

Discovery drafting works best in a rhythm: write forward in bursts, reconcile
in batches. This reference sets the cadence; the reconcile loop
(`reconcile-loop.md`) is what the batch reviews execute.

## Daily targets

Agree on a target with the user at the start of a discovery project and
record the daily rhythm in the `## Notes` or `## Draft Log` body of
`story.md`. Record the book's total in `story.md` as `target-words` and any
due date as `deadline: YYYY-MM-DD`; `story progress .` measures against
both. There is no `draft-target` frontmatter field.

```markdown
## Draft Log

Target: 1500 words/day, or 1 chapter/week.
```

Rules for targets:

- **Words, not quality.** The target measures forward motion. Reconcile
  loops and revision passes are separate scheduled work, not things that
  happen "when the draft feels ready."
- **Small enough to keep daily.** A missed target should be recoverable the
  next day. Chronic misses mean the target is wrong, not the writer —
  renegotiate it.
- **Track streaks, not totals.** Set the daily target as
  `daily-target-words` in `story.md`, and the days the writer plans to write
  as `writing-days` (such as `[mon, tue, thu, fri]`) so rest days never
  break a streak. Run `story progress . --log` at the end of each session: it
  records the day's manuscript word count in `progress.md` and reports
  today's words against the target, the current and longest streak, the
  last four weeks, pace, and a projected finish. Read the streak from that
  report rather than counting it by hand. The log is motivation data, not a
  performance review.

## Batch reviews

Do not reconcile after every writing session if sessions are short — batch
the reconcile loop:

- **After every chapter** is the minimum (the loop's diff step needs a whole
  chapter to be meaningful).
- **Every 3–5 chapters**, run a batch review: re-read the post-hoc notes
  for the batch, check the promise/question ledgers for dangling setups,
  scan for dead ends (see `dead-ends.md`), and confirm the kernel still
  generates momentum.
- **At the midpoint and at draft completion**, run the `revision-continuity`
  developmental checks on the batch before continuing: arc progression,
  pacing, character-state carry-forward.

## Session shape

A discovery session has three phases; keep them separate:

1. **Re-read (10–15 min):** the kernel, the previous chapter's post-hoc
   notes, and the last few pages of prose. No editing — re-reading is for
   voice and momentum, not revision.
2. **Write (the bulk):** forward only. When stuck, cycle back a few hundred
   words and try a different choice. Do not open the bible mid-session —
   note questions in the chapter file as `[TODO: check bible]` and resolve
   them in the reconcile loop.
3. **Close (5 min):** jot a `[TODO]` line above `## Chapter Text` (with
   the outline or post-hoc notes) saying where the next session should
   start ("Mara is about to open the door — decide what's behind it").
   A TODO under `## Chapter Text` is counted and exported as prose.
   Future-you is a different person; leave them a map.

## When cadence breaks

- **Stuck for two sessions:** the chapter may need its kernel refreshed —
  re-read the story kernel and ask what the character wants *right now*.
  Or the reconcile loop was skipped and contradictions are jamming the
  draft: run the loop before writing another word.
- **Draft wandering:** chapters accumulate but nothing deepens — run the
  `theme-craft` working-premise exercise on what the draft actually argues,
  then check whether the next chapter can test that premise.
- **Reconcile backlog:** more than two chapters without a loop means the
  bible is now fiction about a different book. Stop drafting, run the loops
  in order, then resume.
