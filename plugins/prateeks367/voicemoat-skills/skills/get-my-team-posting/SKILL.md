---
name: get-my-team-posting
description: Turn one company message into posts each colleague can publish in their own words, instead of six people posting the same paragraph. Use when a company wants employees posting, a launch needs internal support, or a team was handed copy to share. Do not write one post for everyone to paste, do not write in a voice they would not recognise, and never ask anyone to post what they disagree with.
---

# Get my team posting

Employee advocacy fails the same way every time. One person writes a good post,
sends it to twelve colleagues, and by eleven in the morning the feed shows
twelve identical paragraphs with the same line breaks.

Everyone can see what happened. The company has spent twelve people's
credibility to say one thing once, and the thing it actually communicated is
that none of them meant it.

## Step 1: separate the message from the posts

The message is one sentence everybody agrees is true. That is the only part
that should be identical.

The posts are twelve different things. Write the message down first, on its
own, and get agreement on it before anyone drafts anything.

## Step 2: give each person their own angle

Ask every person what they actually did or saw. Same message, different
evidence:

- The engineer who built the part that was hard
- The person who took the support calls that led to it
- The person who argued against it and changed their mind
- The person who joined halfway and saw it with fresh eyes
- The person who has to sell it and knows the objection

Somebody who cannot answer this should not be posting about it. That is a
perfectly good outcome and it is better than another paraphrase.

## Step 3: write in their words, not the brand's

Ask each person for two things they have already written. A Slack message is
fine. An email is fine. Match that.

The brand voice is for the company account. A person posting in brand voice
reads as the company using their face, which is the thing advocacy was supposed
to avoid.

## Step 4: stagger it

Same message, same morning, same feed is the tell regardless of how different
the wording is. Spread it across days, and let people post at the time they
normally post.

## Step 5: let them say no, and let them disagree

A post somebody was told to publish reads like one. Make declining normal and
say so out loud, because people will assume otherwise.

The strongest advocacy posts usually contain something mildly inconvenient: the
thing that took longer than expected, the feature that is not ready, the
customer who pushed back. Allowing that is what makes the rest believable.

## Step 6: what not to ask for

- Do not organise a block of colleagues to comment on each other's posts. It is
  visible, and it reads exactly as what it is.
- Do not hand out a hashtag list.
- Do not supply a link to paste in the first line without checking what the
  company's own posting guidance says about links.
- Do not ask anyone to post about a customer, a number or a roadmap item that
  has not been cleared. Flag those and stop.

## What this will not do

It will not write the same post twelve ways. If the only difference between
twelve drafts is word order, the answer is fewer posts, not more paraphrases.

It will not ghostwrite in a voice the person has not seen and approved. Every
draft goes to the person named on it before it goes anywhere else.

## What changes when VoiceMoat is connected

Advocacy is a multi-person problem, which is the case a single voice profile
cannot serve:

- `list_profiles` returns the accounts on the team, so each draft is written
  against the right person rather than against a house style.
- `get_voice_profile` gives that person's own trained profile, which is the
  difference between a post in their words and a post with their name on it.
- `score_voice_match` scores each draft against its own author, so twelve posts
  can be checked for sounding like twelve people rather than one.

Team seats are on the Enterprise plan.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
