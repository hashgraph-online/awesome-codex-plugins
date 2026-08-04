---
name: x-thread-builder
description: Build a long-form X (Twitter) thread (tweetstorm) using a 2026 thread formula (listicle-thread, story thread, curiosity-gap opener, how-I teardown), picked by goal (bookmarks, likes, reposts, replies). Structures tweet 1 as a promise plus open loop, paces one beat per tweet, and closes for the repost. Publishes via Publora, which auto-splits long content into a numbered (1/N) thread. Not for single tweets (use x-post-writer) or auditing a draft (use x-humanizer --mode audit).
---

# X Thread Builder

Build tweetstorms that get read all the way down. On X, tweet 1 is the entire
funnel: it has to promise a payoff and open a loop, or no one taps "Show this
thread." Everything after only matters if tweet 1 earns the tap.

## When to use

- User says "turn this into a thread" or "write me a thread about X"
- The idea is a list where each item needs teaching, a story with a build, a
  surprising result with a mechanism, or a repeatable process
- User has a single tweet that is trying to do too much and should be a thread

## Formulas this skill uses (thread shapes)

| Code | Formula | Primary goal | Best for |
|---|---|---|---|
| X7 | Listicle-Thread Promise | bookmarks | numbered teaching thread, one item per tweet |
| X8 | Story Thread | likes, reposts | a real narrative with a build and a turn |
| X9 | Curiosity-Gap Opener | replies, bookmarks | a surprising result, mechanism withheld |
| X10 | How-I Teardown | bookmarks | a repeatable process you ran yourself |

Full skeletons in `../../references/hook-formulas.md`. For single tweets
(X1-X6), use `x-post-writer`.

### Pick by goal first

| Goal | Reach for |
|---|---|
| Bookmarks | X7, X10, X9 |
| Likes | X8 |
| Reposts | X8 |
| Replies | X9 |

## How Publora splits a thread

Pass the full thread as one `content` string. Publora auto-splits it:

- at paragraph breaks (`\n\n`) first,
- then at sentence endings,
- then at word boundaries as a fallback,
- and adds `(1/N)` markers, reserving ~8 chars per tweet for the marker.

For full control of where each tweet breaks, hand-split with a `---` separator
on its own line between tweets. The skill defaults to hand-splitting with `---`
so the user sees exactly how the thread will land before approving.

## Steps

**Voice profile first (all drafts).** If `../../references/voice-profile.md` has `filled: yes`, load it and match the user's voice fingerprint, hard rules, and CTA/link style throughout. If it is not filled, mention once that `x-humanizer --mode profile` can learn their voice from a few posts, then proceed with the generic voice rules.

1. **Gather inputs.** Topic, the raw material (notes, a transcript, a result),
   target audience, and the goal (bookmarks / likes / reposts / replies).
2. **Pick the formula** from the goal table, confirm it fits the material.
3. **Write tweet 1.** This is 80% of the work:
   - Promise a specific payoff (a number, a named result, a clear list count).
   - Open a loop the reader has to resolve ("most people get 3 of them wrong",
     "I did not expect why").
   - Keep it under 280 chars on a standard account. It must stop the scroll
     alone.
4. **Pace the body.** One beat or one item per tweet. Front-load the strongest
   item or beat at position 1-2; tap-through decays with depth. Target 5-9
   tweets for teaching/list threads; longer only for a strong story.
5. **Make each tweet stand alone.** A reader landing mid-thread from a quote
   tweet should still get something.
6. **Write the closer.** The last tweet earns the repost and the follow. End on
   the most quotable line, then one clear ask (bookmark, follow, or "reply with
   yours"), not both.
7. **Humanizer pass** on every tweet. Strip em dashes, AI vocab, uniform rhythm.
   Vary tweet length across the thread.
8. **Optional audit.** Run `x-humanizer --mode audit` on the assembled thread.
9. **Approval card.** Show the thread tweet-by-tweet with per-tweet char counts,
   total tweet count, the formula, and the goal. Confirm any `---` breaks.
10. **On approval.** Call `lib.publish(kind="thread", draft_text=<full thread
    with --- breaks>, target_url="https://x.com/compose/tweet",
    platforms=[<X_PLATFORM_ID>], scheduled_time=<iso_or_None>)`. Publora posts
    the chain in one call and returns a `postGroupId`.

## Hard rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific
rules:

- Tweet 1 must contain a real promise and an open loop. A bare "A thread:" label
  is not a hook.
- Keep each tweet under 280 chars on a standard account (emoji = 2 chars).
- Front-load value. Never bury the best item at the end of a teaching thread.
- No external link in tweet 1. Put links in a later tweet or a reply.
- Vary tweet length. A thread of identical-length tweets reads as AI.
- Only ship a Story Thread (X8) built on a true story. Readers punish
  manufactured stakes.

## Anti-patterns (skill will refuse)

- Tweet 1 that closes its own loop (no reason to expand).
- Over-promising in tweet 1 and under-delivering in the body.
- Vague how-to steps ("be consistent", "add value") in an X10 teardown.
- Padding to hit a round number of tweets.
- Em dashes, AI vocab, ALL CAPS openers.
- Engagement-bait closers ("RT if this helped").

## Resources

- `../../references/hook-formulas.md` - X7-X10 thread skeletons with worked shapes
- `../../references/algorithm-heuristics.md` - thread length, tap-through decay, signals
- `references/thread-structure.md` - per-position pacing and the closer playbook

## Related skills

- `x-post-writer` - when the idea is really just one tweet
- `x-humanizer` - scrub each tweet, or `--mode audit` the whole thread
- `x-hook-extractor` - lift the structure from a viral thread you admire
- `x-content-planner` - schedule threads into a weekly cadence
