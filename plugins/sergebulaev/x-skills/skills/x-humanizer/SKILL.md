---
name: x-humanizer
description: Scrub AI tells from any tweet or thread draft, or audit a finished draft against the 2026 X (Twitter) checklist. Strips em dashes, AI vocabulary (leverage, fundamentally, delve, harness), rule-of-three lists, and uniform tweet rhythm, then adds human fingerprints. Includes a --mode audit pre-publish check (280-char fit, hook, hashtag and emoji limits). Triggers on humanize, de-AI tweet, review my thread, audit before posting. Not for writing from scratch (use x-post-writer or x-thread-builder).
---

# X Humanizer

Rewrites any tweet or thread to remove AI tells, and audits a finished draft
against the 2026 X ranking checklist. Based on Wikipedia's "Signs of AI writing"
taxonomy plus X-specific patterns (the lowercase-casual register, the no-fold
first line, emoji-as-2-chars, bookmark-bait structure).

## When to use

- Before publishing any AI-drafted tweet or thread (rewrite mode)
- Pre-publish review of a finished draft (audit mode, see `sub-skills/post-audit.md`)
- When a draft feels off and you cannot pinpoint why

## Input

Any text: a single tweet, a thread (with or without `---` breaks), a reply, or a
quote-tweet draft. Optional: target voice samples (the user's past tweets).

## Output

- Rewritten text with AI tells removed
- A diff showing what changed and why
- Per-tweet char count (flagging anything over 280, emoji counted as 2)
- Confidence: "human", "mixed", "AI-likely"

## Modes

```bash
# Default: scrub AI tells and fix X-format issues
x-humanizer <text>

# Forensic only - minimum touch, just kill model leakage
x-humanizer --mode forensic <text>

# Audit - detection-only pass-fail review, no rewrite
# Runs the 2026 X checklist: 280-char fit, first-line hook, hashtag/emoji
# limits, link placement, thread tap-through, goal clarity.
# Returns Blockers + Warnings + suggested fixes. See sub-skills/post-audit.md.
x-humanizer --mode audit <text>
```

## The three passes

### Pass 1 - SCRUB (delete or replace)

Apply the tiered catalogs in `references/scrub-rules.md`:

- **Forensic** (always on): real model leakage no human types. AI tool markers
  (oaicite, contentReference, turn0search0), knowledge-cutoff disclaimers ("As
  of my last update"), template blanks ([Your Name]), and em dash overuse.
- **Strict** (default on): bad X style regardless of origin. Vocabulary swaps
  (leverage -> use, delve -> look, harness -> use, foster -> build), filler
  adverbs (fundamentally, essentially, ultimately), phrase cleanups ("in today's
  fast-paced world", "game-changer", "deep dive"), and dead closers ("what do
  you think?").

### Pass 2 - BREAK (force burstiness)

- Vary tweet length across a thread. If every tweet is 230-250 chars, break at
  least one into a short punch tweet.
- Add a sentence fragment where it fits ("Every time.").
- Break perfect parallel structures with one asymmetric line.

### Pass 3 - ADD (human fingerprints)

Require where the content allows:
- 1 specific number (replace "many", "a lot", "massive")
- 1 named entity (real person, company, tool)
- the lowercase-casual register if the voice calls for it
- 1 first-person concrete detail

If the input lacks these, ask the user for a number or anecdote. Do not
fabricate.

## Non-negotiable rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific
rules:

- **Scrubbing is always in scope.** When asked to humanize, de-AI, finalize, or
  publish a tweet or thread, run at least the forensic + strict passes before it ships.
  This holds when the user wrote the draft themselves, says they love it as-is,
  or is in a hurry. Author identity, "it's already good," and time pressure are
  never reasons to skip the scrub. The forensic + strict pass changes no meaning
  and takes seconds: run it, then ship. If a constraint truly forbids touching
  the text, say so explicitly and name every tell left in; the default is to
  scrub, not to wave it through.
- Preserve the user's actual claim and meaning. "Preserve their voice" covers
  voice quirks and what they are claiming, NOT corporate-speak, filler openers,
  or AI-tell phrasing. Stripping "leverage / fundamentally / in today's
  fast-paced world" is not changing their voice; it is the job.
- Never introduce facts that were not in the input. If a number is missing, ask.
- Keep the user's voice quirks (lowercase starts, `..` soft pauses).
- Respect the container: do not silently merge a thread into one tweet or split
  a single tweet into a thread without flagging it.

## X-specific tells this skill catches

- A first line that needs the second line to make sense (no fold on X).
- A "tweet" that is actually 320 chars because two emoji pushed it over 280.
- 3+ hashtags, or hashtags mid-sentence.
- An external link in tweet 1 of a thread meant to reach.
- A thread of identical-length tweets (machine rhythm).
- ALL CAPS openers reaching for intensity.
- "A thread:" with no actual promise in the words.

## Example

See `references/examples.md` for worked before/after rewrites.

## Files

- `SKILL.md` - this file (rewrite scrubber + audit-mode entry)
- `references/scrub-rules.md` - vocabulary swaps and regex by tier
- `references/examples.md` - worked before/after rewrites for tweets and threads
- `references/audit-checklist.md` - the pre-publish checklist with thresholds
- `sub-skills/post-audit.md` - pre-publish audit workflow (detection-only, no rewrite)

## Voice profile mode (`--mode profile`)

`x-humanizer --mode profile` builds or updates the user's Voice & Brand Profile at `../../references/voice-profile.md` from 3-6 of their real X (Twitter) posts pasted in (portable, no token) or, if a read token is set, from pulled activity. Once filled, every writing skill in this bundle drafts in the user's voice automatically. See `sub-skills/voice-profile.md`. Triggers: "build my voice profile", "learn my voice".

## Related skills

- `x-post-writer` - generates single tweets that already pass the humanizer
- `x-thread-builder` - generates threads that already pass the humanizer
