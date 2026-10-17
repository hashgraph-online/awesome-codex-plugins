# X Post Audit

Run any tweet or thread draft through the 2026 X ranking checklist. Catches AI
tells, format violations (280-char fit, emoji counting, hashtags), reach
suppressors (link placement), and structural weaknesses before publishing. This
is the `x-humanizer --mode audit` workflow: detection only, no rewrite.

## When to use

- Before publishing a hand-written or AI-drafted tweet or thread
- When `x-post-writer` or `x-thread-builder` finishes a draft (auto-invoked)
- When a recent post underperformed and the user wants a post-mortem

## Input

- A tweet, or a thread (with or without `---` breaks)
- Optional: target audience, scheduled time, the account tier (standard vs Premium)

## Output

- **Pass / Fail** header
- **Blockers** (must fix before publishing): em dashes over the cap, tweets at
  3+ AI markers, reveal bridges, links in tweet 1, over-length tweets
- **Warnings** (ship-risky): staccato stacks, sincerity markers, missing
  referenced numbers, generic close
- **Suggested fixes** for each issue
- **Per-tweet tell density** (markers, em dashes, fragments, triads). No
  detector score: on tweet-length text those are noise and the skill does not
  promise to beat them
- **Timing recommendation** given the audience

## Checks

### Blockers (auto-fail)

1. More than one em dash in a tweet; en dash between clauses; double dash. A
   single em dash in a tweet that needs it is not a blocker.
2. A single tweet over 280 chars on a standard account (count emoji as 2 chars).
   On Premium, flag only if over 25,000.
3. External link in tweet 1 of a thread, or in a single tweet meant to reach.
4. Opens with "In today's fast-paced world" or similar, a reveal bridge
   ("Here's what", "Stop X, start Y"), or a sincerity announcement ("let me be
   honest", "not gonna lie", "unpopular opinion:" on a popular take).
5. Ends with "What do you think?", "Thoughts?", or "Let that sink in."
6. Any tweet with 3+ vocabulary / grammar markers, or any negative-parallelism
   / "The result?" reveal bridge (see `../references/scrub-rules.md`).
7. First line does not stand alone as a hook (it needs line 2 to make sense).
8. Engagement bait ("RT if you agree", "reply YES").

### Warnings (flag with a suggested fix)

9. 2 or more hashtags, or a hashtag mid-sentence.
10. More than 1 emoji, or any emoji on a serious/contrarian take.
11. A long thread that reads machine-flat (every tweet the same length, no
    clause doing work). Flag that only; never suggest adding variance as a
    tactic. Uniform rhythm in a single tweet is fine (it wins on short posts in
    our corpus).
11a. Staccato stacks ("Short. Punchy. Done.", "No X. No Y. Just Z."), one-word
    lines for drama, more than 2 standalone fragments in a thread, an inserted
    3-word "punch tweet" with no content, or a long/short/long/short seesaw.
12. No odd-precision number with a named referent anywhere the claim would
    allow one (a bare number does not clear this).
13. No named entity (person, company, tool).
14. Stacked or perfectly parallel rule-of-three, a hollow triad without
    concrete items, or a second triad in the same tweet (one natural triad
    passes).
14a. Hedging stack ("perhaps", "it seems") or a framed confession ("ngl this
    hurt: ..."). A flat dated fact is fine.
14b. Over-scrubbed (only when auditing a humanizer rewrite with the original in hand to compare against; a fresh draft that never had an em dash or a triad is not over-scrubbed): uniformly flat tone, lowercase register capitalised, no
    reaction or opinion anywhere.
15. Thread tweet 1 closes its own loop (no reason to expand).
16. The best item or beat is buried at the end of a teaching thread.
17. No clear primary goal: the draft chases replies, reposts, likes, and
    bookmarks all at once. Pick one (see `../../../references/hook-formulas.md`
    "Engagement-goal split").
18. A single tweet trying to carry two ideas (should be two tweets or a thread).

### Info (neutral notes)

19. Suggested posting window given the audience.
20. Single tweet vs thread recommendation given the material.
21. Bookmark-bait opportunity: if the draft is a list/framework/how-to, note that
    it should be structured to maximize saves.

## Steps

1. Detect the container: single tweet, or thread (split on `---` or estimate
   Publora's auto-split).
2. For each tweet, count chars with emoji = 2 and run the blocker checks.
3. If any blockers, return **FAIL** with specific fixes; optionally offer to
   hand off to `x-humanizer` for an auto-rewrite.
4. If no blockers, run the warnings.
5. Report per-tweet tell density. Do not estimate a detector score.
6. Return the structured report with a timing note.

## Related

- `x-humanizer` - proportional rewrite if the audit fails
- `x-post-writer` / `x-thread-builder` - regenerate using a proven formula
