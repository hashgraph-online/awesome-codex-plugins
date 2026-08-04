---
name: x-hook-extractor
description: Reverse-engineer the hook from a viral X (Twitter) tweet or thread URL. Identifies which of the 10 canonical 2026 X formulas it uses (one-liner contrarian, data-point, build-in-public, quote-tweet, mini-list, relatable cold-open, listicle-thread, story thread, curiosity-gap, how-I teardown), explains why it worked, and returns a blank template mapped to your topic with its primary goal. Use to learn from a tweet you admire. Not for writing your own (use x-post-writer or x-thread-builder).
---

# X Hook Extractor

Paste a viral tweet or thread URL. Get back: which hook formula it uses, the
exact structure, why it worked, and a blank template you can fill with your own
voice.

## When to use

- User finds a viral tweet or thread they want to study
- User wants to replicate a specific creator's pattern
- Before `x-post-writer` or `x-thread-builder`, to seed a draft with a proven shape

## Input

An X tweet or thread URL (x.com or twitter.com, `/status/<id>`). For a thread,
the URL of the first tweet is best.

## Output

- **Formula identified** (X1-X10 from `../../references/hook-formulas.md`) with a
  confidence score
- **Container:** single tweet vs thread, and why that container fit the idea
- **Structural breakdown:**
  - The hook line (and for a thread, how tweet 1 opens the loop)
  - Body architecture (per-tweet roles for a thread)
  - The close (what earns the repost or bookmark)
  - Reaction-triggering devices (numbers, named entities, the open loop)
- **Primary goal** the original chased (replies / reposts / likes / bookmarks)
- **Why it worked** psychologically and algorithmically
- **Blank template** with `{slot}` markers matched to the original, ready for the
  user's topic
- **Cautions:** anything in the original that would fail a 2026 audit (em dashes,
  AI vocab, 3+ hashtags, link in tweet 1)

## Steps

1. **Parse the URL.** `lib.url_parser.parse_x_url(url)` returns `handle`,
   `tweet_id`, `url_type`.
2. **Get the text.** This bundle has no built-in tweet reader, so ask the user to
   paste the tweet or the full thread text. (If they later wire an Apify tweet
   actor, read it automatically.)
3. **Detect the container.** One self-contained tweet, or a multi-tweet thread.
4. **Classify against the 11 formulas** using features:
   - Single tweet: a flat contrarian claim (X1)? one hard number (X2)? a personal
     metric/confession (X3)? a quote tweet adding a layer (X4)? a one-line-per-
     item list (X5)? a relatable shared moment (X6)?
   - Thread: a numbered teaching promise (X7)? a story starting at the tension
     (X8)? a surprising result with the mechanism withheld (X9)? a first-person
     "how I" teardown (X10)?
5. **Score confidence.** If two formulas fit, return the top 2 with fit scores.
6. **Extract structure.** Label each part by its role. For a thread, map tweet 1
   (the loop), the front-loaded payoff, the body beats, and the closer.
7. **Name the primary goal** the original optimized for.
8. **Generate a blank template** with `{slot}` markers matched to the original
   shape and the user's topic.
9. **Audit the source.** Flag any AI tells in the original so the user does not
   copy them.

## Example

See `references/examples.md` for worked teardowns.

## Formulas reference

See `../../references/hook-formulas.md` for the 11 canonical X formulas with full
skeletons and goal tags.

## Files

- `SKILL.md` - this file
- `references/classification-rules.md` - feature extraction + scoring heuristics
- `references/examples.md` - worked teardowns (single tweet and thread)

## Related skills

- `x-post-writer` - use the extracted single-tweet template to draft your own
- `x-thread-builder` - use the extracted thread template
- `x-humanizer --mode audit` - audit your draft before shipping
