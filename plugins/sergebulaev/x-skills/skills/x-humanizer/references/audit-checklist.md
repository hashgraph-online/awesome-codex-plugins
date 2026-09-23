# Pre-Publish Audit Checklist (X)

The thresholds the `--mode audit` pass applies. Mirror of the root
`references/algorithm-heuristics.md` checklist, with the humanizer's blocker
distinctions. V3 (2026-09): AI tells are scored by density per tweet; em
dashes are capped at one per tweet, not banned; forced rhythm is a tell. The
scoring unit is the tweet; in a Premium long post (over 280 chars) the unit is
the paragraph, for every check below.

## Blockers (auto-fail)

- [ ] No tweet with more than one em dash (`—`); no en dash (`–`) between
      clauses; no double dash (`--`). A single em dash in a tweet that needs it
      is not a blocker.
- [ ] Single tweet within 280 chars on a standard account (emoji = 2 chars each);
      within 25,000 on Premium.
- [ ] No external link in tweet 1 (single tweet or thread opener).
- [ ] No "In today's fast-paced world" or equivalent opener; no reveal-bridge
      opener ("Here's what", "Stop X, start Y"); no sincerity announcement
      opener ("let me be honest", "not gonna lie", "unpopular opinion:" on a
      popular take).
- [ ] No "What do you think?" / "Thoughts?" / "Let that sink in." dead closer.
- [ ] No tweet (or Premium-post paragraph) with 3+ vocabulary / grammar
      markers (one marker per unit is fine); no "It's not X, it's Y" negative parallelism; no "The result?"
      reveal bridge.
- [ ] First line stands alone as a hook (no fold on X).
- [ ] No engagement bait ("RT if you agree", "reply YES").

## Warnings (flag with fix)

- [ ] 0 or 1 hashtag, at the end.
- [ ] 0 or 1 emoji, none on a serious take.
- [ ] No staccato stacks ("Short. Punchy. Done.", "No X. No Y. Just Z."),
      no one-word lines for drama, at most 2 standalone fragments per thread,
      no inserted 3-word "punch tweet" that carries no content.
- [ ] A long thread does not read machine-flat (every tweet the same length
      and no clause doing work). Flag only that; never suggest adding variance
      as a tactic. A single tweet's uniform rhythm is fine (it wins on short
      posts in our corpus).
- [ ] At least one odd-precision number WITH a named referent where the claim
      allows (a bare number does not clear this).
- [ ] At least one named entity.
- [ ] At most one natural rule-of-three per tweet; no stacked or perfectly
      parallel triads, no hollow triads without concrete items.
- [ ] No hedging stack ("perhaps", "it seems", "I might be wrong but") and no
      framed confession ("ngl this hurt: ..."). A flat dated fact is fine.
- [ ] Only when auditing a humanizer rewrite with the original in hand, not a fresh draft: not over-scrubbed, i.e. the author's tone, reactions, lowercase register and
      one natural triad survived.
- [ ] Thread tweet 1 opens a loop and does not close it.
- [ ] Best item/beat is front-loaded, not buried at the end.
- [ ] One clear primary goal (replies / reposts / likes / bookmarks).
- [ ] One idea per tweet.

## Thresholds quick reference

| Metric | Standard | Premium |
|---|---|---|
| Per-tweet char limit | 280 | 25,000 |
| Emoji char cost | 2 each | 2 each |
| Hashtags | 0-1 | 0-1 |
| Emoji per tweet | 0-1 | 0-1 |
| Em dashes per tweet | 0-1 | 0-1 (about 1 per 100 words in a long post) |
| Vocabulary / grammar markers per unit (tweet; paragraph in a Premium long post) | 0-2 | 0-2 |
| Standalone fragments | 1 per tweet, 2 per thread | same |
| Teaching/list thread length | 5-9 tweets | 5-9 tweets |

## Scoring

- Any blocker -> **FAIL**, return fixes, offer auto-rewrite via `x-humanizer`.
- No blockers, any warnings -> **PASS with warnings**, list each with a fix.
- Clean -> **PASS**, add the timing note and a single tweet vs thread sanity check.
- Report per-tweet tell density (markers, em dashes, fragments, triads). Do
  not estimate a detector score: on tweet-length text those are noise and
  this skill does not promise to beat them.
