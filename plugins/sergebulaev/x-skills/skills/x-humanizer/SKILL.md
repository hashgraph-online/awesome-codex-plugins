---
name: x-humanizer
description: "Remove the AI tells human readers react to in a tweet or thread: 2026 vocabulary by density, reveal bridges, staccato stacks, stacked triads, performed sincerity; caps em dashes at one per tweet. Includes --mode audit (280-char fit, hook, hashtag and emoji limits) and --mode profile. Not for beating AI detectors (no edit reliably does). Not for writing from scratch (use x-post-writer or x-thread-builder). Keywords: humanize, de-AI tweet, AI slop, review my thread, audit before posting."
---

# X Humanizer V3

Rewrites any tweet or thread to remove the AI tells that human readers notice,
and audits a finished draft against the 2026 X ranking checklist. Based on
Wikipedia's "Signs of AI writing" taxonomy, the 2025-2026 stylometry
literature, and our own length-controlled X corpus (n=445). **V3 (2026-09):**
recalibrated on 2026 evidence. Vocabulary is scored by density, em dashes are
capped instead of banned, forced rhythm is now a tell instead of a fix, and
there is an over-correction guard.

**What this skill does not do:** it does not make text "pass" GPTZero,
Pangram, Turnitin or Originality. Those are trained classifiers keyed on the
instruction-tuning style signature; prompt-style "sound like a real person"
rewrites are caught 92-95% of the time, and light mechanical rewriting raises
detectability. On tweet-length text (under 300 words) detector scores are
noise. The real value is elsewhere: expert human readers cite vocabulary (53%)
and sentence structure (36%) as what gives AI text away, and X readers punish
it with the ratio, the quote-dunk, and the scroll. This skill removes what
those readers react to.

## What changed in V3

Evidence tier in brackets: [strong] = replicated across 2+ independent
2025-2026 studies or our own length-controlled corpus; [vendor] = single
platform or vendor dataset; [weak] = one study or expert-panel report.

- **Vocabulary moved from a delete-list to density scoring.** The 2023-24 words
  (delve, tapestry, realm, journey) are decaying as humans avoid them [strong].
  The durable 2026 markers are common words (significant, crucial, notably,
  comprehensive, insights, robust, leverage, foster, landscape, nuanced,
  streamline, elevate) plus grammar: nominalisations and "-ing" clause openers
  at 5.3x the human rate [strong]. In our X corpus AI vocabulary appears in 14%
  of top tweets and those tweets earn 0.58x the median engagement [strong].
  One marker in a tweet is not a verdict. Three is.
- **Em dash is no longer a tell; the density is.** GPT-5.4 emits 1.43 per
  1,000 words, below the 3.23 human baseline [strong]. On X specifically em
  dashes are rare in top tweets (11%) and those tweets earn 0.52x the median
  [strong: corpus], so the cap here is tight: **at most one per tweet**, and
  none in a tweet that does not need one. Replace the excess with a comma, a
  colon, `..`, or a rewrite. Never a period (a split dash stacks fragments).
- **Forced burstiness is the #1 2026 tell, not the fix.** Mechanical
  long/short alternation is a learnable humanizer fingerprint [weak], and on X
  the rhythm rule flips with length: **uniform rhythm wins on short posts**
  (about 75 words, 1.7x median engagement for low-variance tweets) and natural
  variance only helps on long threads (about 430 words, 1.8x) [strong: corpus,
  length-controlled]. So Pass 2 never forces variance on a single tweet, and on
  a thread it only removes manufactured variance and un-flattens what reads
  machine-flat. "Short. Punchy. Done.", "No X. No Y. Just Z.", one-word
  tweets for drama and "The result?" reveals are the current top tells.
- **Rule of three is still a tell, at density.** Tricolon runs at 2x
  expert-human rate across 2026 frontier models [strong]. 26% of top human
  tweets contain exactly one [strong: corpus], so one natural triple with
  concrete items stays. Stacked, perfectly parallel triads and a second triad
  in the same tweet get scrubbed.
- **Fingerprint injection was half wrong.** Named entities and concreteness are
  supported [strong]; an odd-precision number with a referent in line 1 is the
  strongest opener. Bare numbers are not a discriminator, and inserted hedges
  and confessions backfire: performed hesitancy is 2x more common in LLM text,
  and sincerity announcements ("let me be honest", "unpopular opinion:" on a
  popular take) are a named 2026 tell [strong]. Pass 3 asks for a flat, dated,
  uncomfortable fact instead.
- **Over-correction guard.** Humanizer output has its own fingerprint [weak].
  Pass 4 checks whether Passes 1-3 introduced the very patterns they were meant
  to remove. Edits are proportional to real problems. When in doubt, leave it.

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
- Per-tweet tell density (markers per tweet; 3+ triggered a rewrite)
- Reader-read confidence: "reads human", "mixed", "reads AI" (a reader-tell
  estimate, not a detector score)

## Modes

```bash
# Default: scrub AI tells (forensic + strict) and fix X-format issues
x-humanizer <text>

# Forensic only - minimum touch, just kill model leakage
x-humanizer --mode forensic <text>

# Audit - detection-only pass-fail review, no rewrite
# Runs the 2026 X checklist: 280-char fit, first-line hook, hashtag/emoji
# limits, link placement, thread tap-through, goal clarity.
# Returns Blockers + Warnings + suggested fixes. See sub-skills/post-audit.md.
x-humanizer --mode audit <text>

# Profile - build/update the user's Voice & Brand Profile. See the section below.
x-humanizer --mode profile
```

## The four passes

### Pass 1 - SCRUB (score, then delete or replace)

Apply the tiered catalogs in `references/scrub-rules.md`. The unit of
judgement is the **tweet, not the word** (in a Premium long post over 280
chars, the paragraph): count markers per unit, rewrite the unit at 3+, leave a single marker alone unless it is a reveal bridge, negative
parallelism, a sincerity marker, or forensic leakage.

- **Forensic** (always on): real model leakage no human types. AI tool markers
  (oaicite, contentReference, turn0search0), knowledge-cutoff disclaimers ("As
  of my last update"), template blanks ([Your Name]), and em dashes above the
  cap (more than one in a tweet).
- **Strict** (default on): what readers react to. The durable 2026 vocabulary
  set scored by density (significant, crucial, notably, particularly,
  comprehensive, insights, robust, leverage, foster, landscape, nuanced,
  streamline, elevate, empower), grammar markers (nominalisations,
  sentence-opening "-ing" clauses), the 2026 model-idiom layer (quietly, "X
  matters.", compound, "a signal", "the work", "built different", "let that
  sink in"), reveal bridges on a single hit ("The result?", "Here's what",
  "Stop X, start Y", "plot twist:"), all forms of negative parallelism,
  stacked or perfectly parallel triads and any second triad in a tweet, phrase
  cleanups ("in today's fast-paced world", "game-changer", "deep dive"), and
  dead closers ("what do you think?").
- **X-format scrubs** (always apply): 280-char fit with emoji as 2, hashtag and
  emoji limits, link placement, first line that stands alone.

### Pass 2 - RHYTHM (never force it)

Detectors do not score burstiness. On X the corpus says rhythm depends on
length: **uniform rhythm wins on short posts** and natural variance only helps
on long threads. So Pass 2 has two jobs: remove manufactured variance
everywhere, and un-flatten only a long thread that reads machine-flat. It
never adds variance as a tactic.

- **Single tweet, reply, or quote tweet: do not touch the rhythm.** A tweet of
  three same-length sentences is how top tweets read (1.7x median engagement
  for uniform rhythm at about 75 words). Never insert a fragment, never chop a
  sentence to "add punch".
- **Threads:** a mix of tweet lengths that arises from the material is fine and
  is what human variance looks like. Edit only when every tweet runs the same
  length and reads flat, and then let the tweet carrying the most content take
  one real clause, once. Never insert a 3-word "punch tweet" for rhythm; the
  inserted punch is the humanizer fingerprint.
- Standalone fragments: at most 1 per tweet and 2 per thread. "Every time."
  once is a voice quirk; three in a thread is a pattern.
- Banned outright (rewrite as full sentences): "The X? Y." reveals; "No X. No
  Y. Just Z."; "All the X. None of the Y."; "Simple. Effective. Easy."
  adjective stacks; one-word tweets or lines for drama ("Still." "Exactly.");
  pseudo-Socratic Q&A ("Why? Because..."); "Short. Punchy. Done." staccato
  runs. Fragment runs are the tell.
- Layout is not rhythm. A hard return between two short lines is native X
  pacing and stays. Fragment-for-drama inside those lines is the tell.
- Never alternate long/short/long/short across a thread. That seesaw is the
  humanizer fingerprint.

The check is "did I add a staccato pattern, and does any long thread read
machine-flat", not a variance number.

### Pass 3 - ADD (human fingerprints)

Require where the content allows:
- One odd-precision number WITH a named referent: who, what, when, or what it
  cost ("$4,730 in Vercel overages, March invoice", not "$5k" and not
  "massive costs"). A bare number is not a fingerprint; the referent carries
  the signal.
- One named entity (real person, company, date, tool)
- One first-person concrete detail
- One specific, dated, uncomfortable fact stated flat, with no framing sentence
  before or after it. Not "not gonna lie, this one hurt: we lost the client."
  Just "We lost Carta as a client on 14 Feb." The fact carries the
  vulnerability. The frame turns it into performed sincerity, which readers now
  read as the tell.
- The lowercase-casual register if the voice calls for it

Forbidden as openers or pivots (sincerity announcements, a named 2026 tell):
"let me be honest", "I'll be real", "honestly?", "to be direct", "the honest
version is", "real talk", "not gonna lie", "ngl", "can I be vulnerable for a
second", "unpopular opinion:" as a preface to a popular one. Also forbidden as
insertions: hedges the author did not write ("perhaps", "I might be wrong
but", "it seems"). Performed hesitancy is 2x more common in LLM text than in
expert human text; adding it makes the draft read more AI, not less.

If the input lacks these, ask the user for a number, name, or moment. Do not
fabricate.

### Pass 4 - SELF-CHECK (over-correction guard)

Humanizer output has its own fingerprint. Before returning, re-read the result
once and answer three questions:

(a) Did Pass 2 create staccato stacks, "The result?" reveal bridges, one-word
    lines, a punch tweet, or a long/short/long/short seesaw? If yes, merge the
    fragments back into full sentences.
(b) Did Pass 3 add a framed confession, a sincerity announcement, or a hedge
    the author never wrote? If yes, strip the frame and keep only the flat
    fact, or remove the insertion.
(c) Did scrubbing flatten the author's voice: uniform tone, no reaction, no
    concrete detail left, the one natural triad gone, the lowercase register
    capitalised? If yes, restore what the author had.

If any answer is yes, dial back rather than scrub harder. Edits must be
proportional to real problems: a clean tweet gets one or two touches, not a
quota. When in doubt whether a pattern is the author or the model, leave it.

## Non-negotiable rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific
rules (V3):

- **Scrubbing is always in scope.** When asked to humanize, de-AI, finalize, or
  publish a tweet or thread, run at least the forensic + strict passes before it ships.
  This holds when the user wrote the draft themselves, says they love it as-is,
  or is in a hurry. Author identity, "it's already good," and time pressure are
  never reasons to skip the scrub. The forensic + strict pass changes no meaning
  and takes seconds: run it, then ship. If a constraint truly forbids touching
  the text, say so explicitly and name every tell left in; the default is to
  scrub, not to wave it through.
- **Scrub proportionally.** A pass that finds nothing changes nothing. Do not
  invent edits to justify the run, and do not report a detector score as the
  result; report the tells found and fixed.
- Preserve the user's actual claim and meaning. "Preserve their voice" covers
  voice quirks and what they are claiming, NOT reveal bridges, staccato stacks,
  or a tweet with 3+ vocabulary markers. Stripping those is not changing their
  voice; it is the job.
- Never introduce facts that were not in the input. If a number is missing, ask.
- Never introduce sincerity markers, hedges, or confessional frames. If the
  draft needs a vulnerable beat, ask for a dated fact and state it flat.
- Keep the user's voice quirks (lowercase starts, `..` soft pauses, one em dash
  in a tweet that needs it, one natural triad).
- Never promise detector results. If the user asks "will this pass GPTZero,"
  answer honestly: nobody can promise that, and the score on a 280-char tweet
  is noise.
- Respect the container: do not silently merge a thread into one tweet or split
  a single tweet into a thread without flagging it.

## X-specific tells this skill catches

- A first line that needs the second line to make sense (no fold on X).
- A "tweet" that is actually 320 chars because two emoji pushed it over 280.
- 3+ hashtags, or hashtags mid-sentence.
- An external link in tweet 1 of a thread meant to reach.
- A thread with an inserted 3-word "punch tweet" for rhythm (the humanizer
  fingerprint), or a long thread where every tweet reads machine-flat.
- ALL CAPS openers reaching for intensity.
- "A thread:" with no actual promise in the words.
- "Unpopular opinion:" on a take that is actually popular.

## Example

See `references/examples.md` for worked before/after rewrites.

## Files

- `SKILL.md` - this file (rewrite scrubber + audit-mode entry)
- `references/scrub-rules.md` - V3 regex patterns by tier, density scoring, em dash cap, rhythm rules, forbidden insertions
- `references/examples.md` - worked before/after rewrites for tweets and threads
- `references/audit-checklist.md` - the pre-publish checklist with thresholds
- `sub-skills/post-audit.md` - pre-publish audit workflow (detection-only, no rewrite)
- `sub-skills/voice-profile.md` - build/update the user's Voice & Brand Profile (`--mode profile`)
- `sub-skills/illustration.md` - optional Pixfaro image workflow

## Voice profile mode (`--mode profile`)

`x-humanizer --mode profile` builds or updates the user's Voice & Brand Profile at `../../references/voice-profile.md` from 3-6 of their real X (Twitter) posts pasted in (portable, no token) or, if a read token is set, from pulled activity. Once filled, every writing skill in this bundle drafts in the user's voice automatically. See `sub-skills/voice-profile.md`. Triggers: "build my voice profile", "learn my voice".

## Related skills

- `x-post-writer` - generates single tweets that already pass the humanizer
- `x-thread-builder` - generates threads that already pass the humanizer
