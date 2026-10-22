---
name: define-my-content-pillars
description: Work out the three to five subjects someone can post about repeatedly without running dry, from what they have already published and what they actually know. Use when someone asks what they should post about, says they have run out of ideas, wants content pillars or themes, or is starting an account and does not know where to aim. Do not use it to plan dates or write posts.
---

# Define my content pillars

Running out of ideas is almost never a shortage of ideas. It is a missing
answer to "what am I the person for", so every post starts from nothing.

Pillars fix that by making the question smaller. Not "what should I post today"
but "which of my four subjects, and what about it".

## Step 1: gather the evidence, not the aspiration

Ask for both, because they are usually different:

- **Ten to fifteen posts they have already written**, ordinary ones. What they
  actually return to is more honest than what they think they write about.
- **What they want to be known for**, in their own words.

Then the question people skip: **who is reading, and what do they want?** A
pillar nobody needs is a diary entry.

If they have no posts yet, work from what they do for a living, what people ask
them, and what they argue about.

## Step 2: cluster what is already there

Group the posts by subject. Report the actual distribution, including the
uncomfortable parts: they think they write about hiring and eleven of fifteen
posts are about tooling. That gap is the most useful thing in this exercise.

## Step 3: test each candidate pillar against four questions

A pillar earns its place only if all four hold:

1. **Can you write fifty posts about this?** If it runs out at five, it is a
   topic, not a pillar.
2. **Do you know something first-hand?** Not "have opinions about". Have done.
3. **Does the reader want it?** Interesting to you is not sufficient.
4. **Would someone else write it differently?** If your version is
   interchangeable with the generic version, it will read as filler.

Say plainly which candidates fail and on which question.

## Step 4: land on three to five, and make them specific

"Marketing" is not a pillar. "Why small teams should not run paid ads before
they have organic proof" is.

For each pillar give:

- A one-line definition
- The angle only this person can take
- Five seed ideas, to prove the pillar has depth rather than asserting it
- One thing it is not, to keep the edges sharp

Three to five. Two is monotony, seven is no focus at all.

## Step 5: say what to drop

The valuable half of this exercise is subtraction. Name the subjects they
should stop posting about, and why: no first-hand knowledge, no audience
interest, or indistinguishable from everyone else.

## What changes when VoiceMoat is connected

Step 2 is only as good as the fifteen posts someone chose to paste, and people
paste the ones they liked, which quietly skews the whole thing.

- `list_posts` and `get_post` supply the real history rather than a
  self-selected sample, including the posts they would not have shown you.
- `get_analytics` and `list_posts` give the engagement behind each post, so
  once the posts are grouped a pillar can be tested against what the audience
  actually responded to instead of what the writer enjoyed writing.
- `get_voice_insights` returns the vocabulary and patterns that recur across
  everything they have written, which often names a pillar they did not know
  they had.
- `get_post_ideas` fills each agreed pillar with seeds in their own voice, so
  step 4 is generated rather than guessed.

Once the pillars are set, the plan-my-week skill turns them into a dated
calendar.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
