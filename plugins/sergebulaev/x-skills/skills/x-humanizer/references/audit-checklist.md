# Pre-Publish Audit Checklist (X)

The thresholds the `--mode audit` pass applies. Mirror of the root
`references/algorithm-heuristics.md` checklist, with the humanizer's blocker
distinctions.

## Blockers (auto-fail)

- [ ] No em dash (`—`), en dash (`–`), or double dash (`--`).
- [ ] Single tweet within 280 chars on a standard account (emoji = 2 chars each);
      within 25,000 on Premium.
- [ ] No external link in tweet 1 (single tweet or thread opener).
- [ ] No "In today's fast-paced world" or equivalent opener.
- [ ] No "What do you think?" / "Thoughts?" dead closer.
- [ ] No AI vocabulary blacklist words.
- [ ] First line stands alone as a hook (no fold on X).
- [ ] No engagement bait ("RT if you agree", "reply YES").

## Warnings (flag with fix)

- [ ] 0 or 1 hashtag, at the end.
- [ ] 0 or 1 emoji, none on a serious take.
- [ ] Thread tweets vary in length (not all within ~20 chars).
- [ ] At least one specific number where the claim allows.
- [ ] At least one named entity.
- [ ] No rule-of-three list without concrete items.
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
| Teaching/list thread length | 5-9 tweets | 5-9 tweets |

## Scoring

- Any blocker -> **FAIL**, return fixes, offer auto-rewrite via `x-humanizer`.
- No blockers, any warnings -> **PASS with warnings**, list each with a fix.
- Clean -> **PASS**, add the timing note and a single tweet vs thread sanity check.
