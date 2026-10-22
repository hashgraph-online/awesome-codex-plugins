---
name: same-idea-both-platforms
description: Turn one idea into a Twitter post and a LinkedIn post that read as if written separately, rather than the same text pasted twice. Use when someone wants to post the same thing on both platforms, asks to adapt a post for the other platform, or asks how something should differ between Twitter and LinkedIn. Do not use it to write for one platform only.
---

# Same idea, both platforms

Cross-posting fails in a specific and visible way. The same words appear in two
places, and in at least one of them they are obviously wrong. A LinkedIn post
dropped onto Twitter reads as a press release. A tweet dropped onto LinkedIn
reads as a fragment.

The idea travels. The writing does not.

## Step 1: find the idea underneath

Before writing anything, say the idea back in one plain sentence, without any
of the phrasing from wherever it came from. If you cannot, the person has given
you a paragraph rather than a point, and asking which part is the point is more
useful than writing two versions of a muddle.

## Step 2: write the two posts separately

Do not write one and adapt it. Write each from the idea, because adaptation is
how the seams get left in.

**Twitter.** Compression is the whole game. The first line has to work alone,
because that is often all anyone sees. Cut the setup. A tweet can start in the
middle of the thought. Lower case, fragments and a flat unhedged claim all
belong here.

**LinkedIn.** Context is expected, and readers arrive with less shared
background. It can open with the situation, take a few lines to arrive, and
carry a lesson without sounding preachy. Line breaks do the work paragraphs do
elsewhere. It tolerates length only if each line pays.

## Step 3: check the seams

Read both back and look for the specific tells:

- Twitter phrasing surviving into LinkedIn: "hot take", a thread numbering, a
  fragment that needed the previous tweet.
- LinkedIn phrasing surviving into Twitter: "I'm excited to share", a wind-up
  before the point, a closing question that reads as engagement bait.
- The same distinctive sentence in both. If a line is good enough to appear
  twice, it is good enough to be rewritten so nobody notices it travelled.

## Step 4: hand over both, and say what differs

Give both posts, then one line on what you changed and why. People cross-post
badly because they think the difference is length. Show them it is structure.

## What changes when VoiceMoat is connected

This is the workflow that gains the most from connecting, because VoiceMoat
holds your two platforms separately rather than as one setting:

- `get_voice_profile` is **per platform**. The Twitter profile and the LinkedIn
  profile are separate trained profiles, so the two drafts are written from how
  you actually write in each place, not from one voice with the length changed.
- `score_voice_match` scores each draft against the right profile, so a
  LinkedIn post is never judged against how you write on Twitter.
- `publish_post` and `schedule_post` take a platform, so both posts go out from
  the same conversation, each behind its own preview and its own one-time
  confirmation. Two posts means two approvals, deliberately.

Never make the second call on your own. Show the person the exact preview the
first call returns and wait for a clear yes before you send the one-time code
back. Never make both calls in one step.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
