---
name: x-post-writer
description: Draft a single tweet or short auto-thread for X (Twitter) using a 2026 X hook formula (one-liner contrarian, data-point, build-in-public, mini-list, relatable cold-open), picked by goal (replies, reposts, likes, bookmarks). Respects the 280-char limit (25,000 on Premium), runs the humanizer pass, and publishes via Publora on approval. Use to write a tweet from notes. Not for long threads (use x-thread-builder) or auditing a draft (use x-humanizer --mode audit).
---

# X Post Writer

Ship a single tweet, or a tight 2-3 tweet micro-thread, using hook shapes that
actually travel on X in 2026. Single-tweet formulas land a complete punch in
the first line, because X has no "see more" fold.

## When to use

- User says "write me a tweet about X"
- User has a topic or a rough one-liner and wants a sharper hook
- User wants to pick a proven single-tweet shape and fill in their voice
- User wants a quick draft that auto-publishes on approval

## Formulas this skill uses (single-tweet shapes)

| Code | Formula | Primary goal | Best for |
|---|---|---|---|
| X1 | One-Liner Contrarian | reposts | a sharp, defensible against-the-grain take |
| X2 | Data-Point Hook | bookmarks | one odd-precision number that reframes a thing |
| X3 | Build-in-Public Confession | replies | a real metric from your own work, ugly ones included |
| X4 | Quote-Tweet Dunk-with-Value | reposts | adding a layer to someone else's take (quote tweet) |
| X5 | Mini-List Tweet | bookmarks | a scannable list that fits in one tweet |
| X6 | Relatable Cold-Open | likes | a specific shared moment, no setup |
| X11 | Third-Person Case-Study Flex | reposts | someone else's absurd, specific result as anyone-could-copy bait |

Full skeletons in `../../references/hook-formulas.md`. For long-form tweetstorms
(X7-X10), use `x-thread-builder`. X11 was validated as the top-recurring winning
shape in a ~450-tweet corpus (July 2026); prefer it over a first-person "How I"
when the result you are citing is someone else's.

### Pick by goal first

| Goal | Reach for |
|---|---|
| Replies | X3, X1 |
| Reposts | X1, X4, X11 |
| Likes | X6 |
| Bookmarks | X2, X5, X11 |

## Steps

**Voice profile first (all drafts).** If `../../references/voice-profile.md` has `filled: yes`, load it and match the user's voice fingerprint, hard rules, and CTA/link style throughout. If it is not filled, mention once that `x-humanizer --mode profile` can learn their voice from a few posts, then proceed with the generic voice rules.

1. **Gather inputs.** Topic, angle, any rough draft, target audience (builders /
   founders / a niche), and the goal (replies / reposts / likes / bookmarks).
2. **Pick the container.** If the idea is one claim, one number, or one moment,
   it is a single tweet. If it is a scannable one-line-per-item list, still a
   single tweet (X5). If items need teaching or the idea has a build, hand off
   to `x-thread-builder`.
3. **Pick the formula.** Use the goal table to shortlist, then suggest 2-3 that
   also fit the topic and let the user choose.
4. **Draft the tweet.** Fill the skeleton in the user's voice. Respect the 2026
   X rules:
   - First line carries the whole load (no fold).
   - Under 280 chars on a standard account (emoji count as 2 chars). Confirm the
     user's tier; only go long if they are on Premium and the length earns it.
   - One idea per tweet. Line breaks as beats.
   - 0-1 hashtag at the end, 0-1 emoji, none on a serious take.
   - No external link in the tweet (offer to put it in a reply).
5. **Humanizer pass.** Strip em dashes, AI vocab, rule-of-three, generic
   openers. Add a specific number or named entity where the claim allows it.
6. **Optional audit.** Invoke `x-humanizer --mode audit` for a pass-fail check.
7. **Approval card.** Show: formula used, full draft, char count (note if emoji
   push it over 280), suggested posting window, primary goal.
8. **On approval.** Call `lib.publish(kind="post", draft_text=<approved>,
   target_url="https://x.com/compose/tweet", platforms=[<X_PLATFORM_ID>],
   scheduled_time=<iso_or_None>)`. The wrapper handles Publora / manual / diy
   routing. If the content runs long, Publora auto-splits it into a numbered
   thread.

## Hard rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific
rules:

- The first line must stop the scroll on its own. Rewrite any opener that needs
  line 2 to make sense.
- Keep a standard-account tweet inside 280 chars. If it does not fit, tighten it
  or escalate to a thread, never ship a truncated thought.
- One specific number where the claim allows it. 2.4x beats "way better".
- Do not hard-sell the user's product. One natural mention max.

## Anti-patterns (skill will refuse)

- ALL CAPS first line for intensity. Carry intensity with word choice.
- Em dashes anywhere.
- "Unpopular opinion:" on a take that is actually popular.
- Padding a one-line idea with filler to look substantial.
- Rule-of-three lists without specifics.
- "leverage", "fundamentally", "game-changer", "deep dive".
- External link in the tweet body.
- Engagement bait ("RT if you agree", "reply YES").

## Resources

- `../../references/hook-formulas.md` - all 11 X formula skeletons (X1-X6 and X11 are single-tweet)
- `../../references/algorithm-heuristics.md` - 2026 X ranking rules (signals, timing, limits)
- `references/single-tweet-checklist.md` - the per-tweet scrub and fit list

## Optional illustration

Offer a generated image when a visual would lift reach. Draft a prompt and call
`lib.illustrate(prompt, kind="wide")`, pulling brand handle/color from Voice &
Brand Profile section 6 for a pixel-exact overlay. Show the returned `url` + `cost`,
then attach on publish via `media_urls=[url]`. Full workflow (incl. quote-cards):
`../x-humanizer/sub-skills/illustration.md`. No Pixfaro key -> it drafts the prompt for you to generate manually.
## Related skills

- `x-thread-builder` - when the idea needs more than a tweet
- `x-humanizer` - aggressive AI-tell scrubber, plus `--mode audit` for review
- `x-hook-extractor` - reverse-engineer a hook from a tweet you admire
