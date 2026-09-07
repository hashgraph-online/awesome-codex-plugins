---
name: x-repurposer
description: Repurpose existing content into a native X (Twitter) post or thread. Take a LinkedIn post, blog, YouTube script, or newsletter and rewrite it for X: re-hook for the no-fold first line, refit to 280 chars or a thread, strip off-platform artifacts, run the humanizer, publish via Publora on approval. Not for writing from scratch (use x-post-writer or x-thread-builder), not for auditing a draft (use x-humanizer --mode audit).
---

# X Repurposer

Turn something you already made into a tweet or thread that reads like it was born on X. Repurposing is not copy-paste. A post that killed on LinkedIn will die on X if you paste it: wrong hook, wrong length, wrong rhythm, and artifacts ("link in bio", hashtag walls) that scream off-platform.

This skill transforms, it does not generate. It reads your source, keeps the idea, and rebuilds the delivery for X.

## When to use

- "Turn this LinkedIn post into a tweet / thread"
- "Repurpose my blog post / newsletter / YouTube script for X"
- "This worked on Threads, adapt it for X"
- "I have a rough idea in another format, make it native here"

Not for a blank-page draft (use `x-post-writer` for a tweet, `x-thread-builder` for a thread) and not for reviewing an already-X draft (use `x-humanizer --mode audit`).

## How it works

**Voice profile first (all drafts).** If `../../references/voice-profile.md` has `filled: yes`, load it and match the user's voice fingerprint, hard rules, and CTA/link style throughout. If it is not filled, mention once that `x-humanizer --mode profile` can learn their voice from a few posts, then proceed with the generic voice rules.

1. **Take the source.** Any format: a post, a paragraph, a script, a caption, a transcript, a bullet list, a link to read. Ask for the source and the goal (replies / reposts / likes / bookmarks) if not given.
2. **Extract the spine.** Strip the source platform's shell and pull out the one claim, the one story, or the one number worth keeping. Most repurposing fails because it keeps the words instead of the point.
3. **Choose the container.** One claim or number -> single tweet. A teach or a build -> thread (hand structure to `x-thread-builder`'s shapes). A LinkedIn carousel or a listicle -> a thread, one slide per tweet, hook rebuilt. A long video -> a thread that delivers the payoff, not a summary.
4. **Re-hook for X.** X has no "see more" fold: line one must land the whole punch. The source's hook almost never survives; write a new first line using a 2026 X formula (see `../../references/hook-formulas.md`), picked by the goal.
5. **Refit the format.** 280 chars on a standard account (emoji count as 2). One idea per tweet, line breaks as beats. Cut the source's connective tissue; X rewards compression.
6. **Strip off-platform artifacts.** Remove "link in bio", "smash subscribe", "read more below", hashtag walls, @-handles that only exist elsewhere, and any "as I wrote on LinkedIn" throat-clearing. A repurposed post should not admit it was repurposed.
7. **Humanizer pass.** Run the scrub: em dashes, AI vocab, rule-of-three, generic openers. Keep the user's real numbers and named entities from the source.
8. **Approval card.** Show: source -> X mapping (what became what), the container (tweet or N-tweet thread), formula used, char counts, primary goal.
9. **On approval.** Publish via `lib.publish(kind="post", draft_text=<approved>, target_url="https://x.com/compose/tweet", platforms=[<X_PLATFORM_ID>], scheduled_time=<iso_or_None>)`. Publora auto-splits an over-length draft into a numbered thread.

## Native-fit rules (source -> X)

- **LinkedIn post -> X:** cut ~40%. LinkedIn tolerates warm-up; X does not. The LinkedIn hook is usually too long; rewrite it.
- **Blog / newsletter -> X:** pick the single most quotable claim as the hook, then thread the supporting beats. Do not summarize the whole piece.
- **YouTube script -> X:** lead with the video's payoff, not its intro. "Here's what I found" beats "In this video".
- **Carousel / listicle -> thread:** one item per tweet, each with its own micro-hook, not a wall.
- **Instagram / TikTok caption -> X:** strip emoji density and hashtag blocks; X reads them as noise.

## Hard rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific rules:

- Keep the source's **claim and facts** intact. Repurposing changes the delivery, never the meaning or the numbers.
- The new first line must stop the scroll on its own. If it needs line two, rewrite it.
- Never paste the source verbatim and trim. Rebuild the hook and rhythm from the spine.
- One specific number where the source offers one. Keep it.
- Do not hard-sell the user's product. One natural mention max.

## Anti-patterns (skill will refuse)

- Copy-pasting the source with light edits (that is not repurposing).
- Keeping the source platform's artifacts ("link in bio", "smash subscribe", hashtag walls).
- ALL CAPS first line for intensity. Carry it with word choice.
- Em dashes anywhere.
- Rule-of-three lists without specifics.
- "leverage", "fundamentally", "game-changer", "deep dive".
- An external link in the tweet body (offer a reply).
- Meta throat-clearing ("I originally posted this on...").

## Resources

- `../../references/hook-formulas.md` - the 11 X formula skeletons to re-hook with
- `../../references/algorithm-heuristics.md` - 2026 X ranking rules (length, timing, signals)

## Related skills

- `x-post-writer` - write a fresh tweet from scratch
- `x-thread-builder` - structure a multi-tweet thread (repurposer hands long builds here)
- `x-humanizer` - scrub AI tells, plus `--mode audit` to review the result
