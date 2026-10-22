---
name: sound-less-like-ai
description: Rewrite text so it stops reading as machine-written, by naming the specific tells and removing them. Use when someone says a draft sounds like AI, sounds generic, sounds corporate, or asks to humanise or de-AI a piece of writing. Do not use it to help anyone pass off writing as human where being honest about authorship matters, such as academic work or disclosures.
---

# Make this sound less like AI

"Sounds like AI" is not a vague feeling. It is a short list of habits, and once
you can name them you can remove them. Most attempts fail because they add
personality on top instead of removing the tells underneath.

## Step 1: name the tells, out loud, with quotes

Go through the text and point at the specific things, quoting each one. Do not
just report a general impression.

**Rhythm**

- Every sentence roughly the same length. Human writing is lumpy: a long one,
  then four words.
- Three-part lists everywhere. "Clear, concise, and compelling." Once is fine.
  Three times in a page is a fingerprint.
- Every paragraph the same size.

**Hedging and padding**

- "It is important to note", "arguably", "can help you to", "in today's fast
  paced world".
- Sentences that restate the previous sentence in different words.
- A closing paragraph that summarises what was just said.

**Vocabulary**

- delve, leverage, robust, seamless, landscape, testament, tapestry, unlock,
  elevate, resonate, foster, navigate, realm.
- The em-dash used as the only punctuation for a pause, several times a page.
- "Not just X, but Y" as a recurring shape.

**Substance**

- No names, no numbers, no dates, nothing that could be checked.
- Advice that is true for everyone and therefore useful to no one.
- Confidence with nothing at stake. No admission, no uncertainty, no cost.

## Step 2: cut before you add

Delete the padding first, then reread. Text often sounds human as soon as the
filler leaves, and anything you add before cutting is just decoration on top of
the problem.

## Step 3: put something real in

The deepest tell is that nobody is in the text. Ask for one of these and use it:

- A specific number, price, date or duration
- A named tool, place or person
- Something that went wrong, and what it cost
- An opinion the writer would defend in a room

One concrete detail does more than a paragraph of voice.

## Step 4: break the rhythm on purpose

Vary sentence length hard. Let one run and the next be three words. Start a
sentence with And or But if that is how the person talks. Leave a slightly
awkward phrasing in if it is theirs. Perfectly smooth is itself a tell.

## Step 5: say what you changed

List the tells you removed, with the before and after. The person should be able
to catch these themselves next time, which is the actual point.

‼️ Two things to refuse. Do not claim the result will beat an AI detector,
because those tools are unreliable in both directions and the claim is not
yours to make. And do not help disguise authorship where being honest about it
matters, such as academic submissions or disclosures.

## What changes when VoiceMoat is connected

Everything above gets you to writing that sounds human. It does not get you to
writing that sounds like **you**, and those are different targets. Generic
human is still generic.

- `get_voice_profile` gives the actual register to aim at: your tone, your
  rhythm, your vocabulary and the phrases you never use.
- `score_voice_match` scores the rewrite from 0 to 100 against that profile.
  This is the part that matters: text can read perfectly human and still score
  low because it is somebody else's human.
- `improve_post` runs a deeper pass on a real draft when the problem is
  structural rather than cosmetic.

There is also a free browser version of the before and after at
voicemoat.com/tools/humanize-ai-text, if you want to see the tells highlighted
without installing anything.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
