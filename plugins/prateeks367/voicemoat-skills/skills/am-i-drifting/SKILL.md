---
name: am-i-drifting
description: Compare how someone writes now against how they used to write, and name what has changed. Use when someone asks whether they still sound like themselves, whether their posts have got worse or blander, whether AI has flattened their writing, or wants their recent posts compared with their older ones. Do not use it to compare one person against another person.
---

# Am I drifting from my voice?

Voice does not collapse in one post. It erodes: a hedge added here, a
flourish borrowed there, a habit picked up from whatever everyone else was
posting that month. By the time it is obvious, it has been happening for
months.

This workflow finds the drift by comparing a person against their own past,
never against a general standard of good writing.

## Step 1: get two samples, far apart

Ask for:

- **Five posts from when they felt they were writing well.** Six months ago, a
  year, whenever they name.
- **Five of their most recent posts.**

The gap matters more than the count. Ten posts from the same fortnight will
show you nothing.

If they cannot produce the older set, say plainly that you can describe how
they write now but cannot tell them what has changed, and stop there rather
than inventing a trend.

## Step 2: describe each period separately

Before comparing, characterise each set on its own terms, so you are not just
hunting for differences you already expect:

- Openings, and how the first line earns the second
- Sentence and paragraph length
- Vocabulary, especially words that recur
- How much of the person is in it: opinions, specifics, admissions, names,
  numbers
- Structure: does it argue, tell, list, or teach

## Step 3: name what changed, and be specific

Vague drift reports are useless. "Your writing feels less personal" tells them
nothing they can act on. This does:

> Four of your five older posts open with something that happened to you. None
> of the recent five do; three open with a general claim about the industry.

Look especially for the failure modes that actually happen:

- **Hedging.** Qualifiers arriving where there used to be a flat statement.
- **Abstraction.** Specific stories replaced by general principles.
- **Length creep.** Posts getting longer without getting denser.
- **Borrowed register.** Sentence shapes that belong to whoever is currently
  loud in their niche.
- **Sanding down.** The odd, particular, slightly awkward phrasings that made
  them recognisable, gone.

## Step 4: say whether it matters

Not all drift is decay. People deliberately change register when they change
audience, get a new job, or get bored of a persona. Ask before diagnosing.

Then give them, at most, three concrete things to put back. Not a rewrite of
their voice, three habits.

‼️ Do not produce a score. Ten posts is not a measurement, and a number here
would be invented precision about something the person cares about.

## What changes when VoiceMoat is connected

The comparison above depends on which posts someone happens to remember to
paste, which is the weakest part of it. Connected to VoiceMoat:

- `get_voice_insights` returns the Voice Lab analysis for the account:
  dominant patterns, hook style, sentence rhythm and vocabulary, measured over
  the whole history rather than five samples.
- On Twitter it also returns the **Voice Guard drift read**: a status, a score,
  and the specific areas where recent posts have moved away from the trained
  baseline, ranked by severity. That is a real comparison against everything
  the account has posted, not against five posts pasted from memory.
- `list_posts` and `get_analytics` show whether the drift cost anything, by
  putting the change next to what the posts actually did.

Two limits, stated rather than left to be discovered:

- **The Voice Guard drift read is Twitter only today.** On LinkedIn you get the
  Voice Lab analysis and the posts, which is still a far better sample than
  pasting, but not the scored drift comparison.
- Both need Voice Lab to have been run on the account. If it has not been, the
  tools return empty rather than guessing, and the honest answer is to go and
  run it.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
