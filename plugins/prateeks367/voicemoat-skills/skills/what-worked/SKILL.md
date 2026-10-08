---
name: what-worked
description: Work out what a person's best-performing Twitter or LinkedIn posts have in common, and turn that into what to write next. Use when someone asks why a post did well or badly, what their best posts have in common, what to write more of, or wants their recent posts reviewed against their numbers. Do not invent engagement numbers, and do not use this to analyse someone else's account.
---

# What worked, and more of it

The useful version of this is specific to one person's actual posts. General
content advice is free everywhere and worth what it costs.

## Step 1: get the numbers

Ask them to paste their **last ten to fifteen posts with their numbers**: the
text, and impressions plus likes or reactions plus comments for each. Both
Twitter and LinkedIn let them see this in their own analytics.

If they can only give you a handful, work with it and say what that limits.

‼️ Never state a number they did not give you. Not an estimate, not a
benchmark, not a typical engagement rate for their industry. If you do not have
it, say you do not have it. One invented figure makes every real one suspect.

## Step 2: compare like with like

Before drawing conclusions, sort out what is actually comparable:

- **Rate, not raw count.** A post with 400 likes on 90,000 impressions did
  worse than one with 60 likes on 3,000. Work in engagement per impression
  wherever they have gave you impressions.
- **Format against format.** A text post, an image post, a thread and a link
  post do not compete on level terms on either platform.
- **Age.** A post from yesterday has not finished. Do not rank it against one
  from three weeks ago.
- **Outliers.** One post that went unusually wide often did so for a reason
  that will not repeat. Name it and set it aside rather than building a theory
  on it.

## Step 3: say what the winners share

Look at the top few against the bottom few and find the differences that are
actually in the writing:

- How the first line works
- Length and structure
- Whether it makes a claim, tells a story, asks something, or teaches
- Subject matter
- Whether it invites a reply

Say what they share in plain words, and be honest about the strength of it.
Three posts is a hint. Ten is a pattern worth acting on. Say which one you have.

If the honest answer is that there is no pattern, say that. It is more useful
than a confident theory built on four posts, and they will find out either way.

## Step 4: turn it into the next post

Only once they have agreed the pattern is real:

- Suggest three to five specific things to write next, in the shape that
  worked, on subjects they have signalled they know about.
- Offer opening lines in the style of whichever of their own posts opened best.

Do not turn this into a full drafting session unless they ask. If they want
posts written, that is the write-in-my-voice workflow.

## What changes when VoiceMoat is connected

Everything above works from pasted numbers. With a VoiceMoat account
connected, steps 1 and 2 stop being manual:

- `get_analytics` returns impressions, reactions, replies and post count for a
  window you choose, for the connected account, with no pasting.
- `list_posts` returns the actual best performers for that window, and
  `get_post` returns the full text and exact figures for any one of them.
- Because the data comes from the account rather than from what someone
  remembered to paste, the comparison in step 2 covers everything they posted,
  including the ones they would rather forget.

One caveat VoiceMoat states rather than hides: LinkedIn's post analytics API is
gated behind its Community Management partner programme, which VoiceMoat has
not been approved for, so LinkedIn figures arrive through the VoiceMoat browser
extension and are only as fresh as the last time it ran. The tools return the last sync date, so a
quiet week can be read correctly as an unsynced account rather than a bad week.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
