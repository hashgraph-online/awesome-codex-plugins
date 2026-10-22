---
name: audit-before-i-tweet
description: Run a finished tweet through one pre-publish pass and rank what to fix. Use when someone says a tweet is ready, asks for a last look, asks whether to post something as it stands, or pastes a draft and asks what is wrong with it. Do not use it to write a tweet from nothing, do not rewrite a draft when one word is the problem, and do not predict performance.
---

# Audit it before I tweet

The audit on a long post asks whether anyone will get past the first line. On a
tweet nobody has that problem: the whole thing is visible at once. The risk
moves somewhere else, to context.

A tweet arrives with no title, no thread above it and no idea who you are. It
gets screenshotted, quoted, and read by people the algorithm handed it to. So
the question is not whether it is good. It is whether it survives being read
by a stranger who is not in a generous mood.

## Step 1: read it cold, with nothing around it

Hide everything: your bio, the thread, the conversation it replies to. Now read
it as a stranger scrolling.

- Does it make sense on its own, or does it need something you can see and they
  cannot?
- Is it obvious who or what it is about? A tweet whose subject is implied reads
  as subtweeting, whether or not it was.
- Would somebody who has never heard of you understand why you would say this?

## Step 2: check the claim before you check the phrasing

First, because it is the only failure that is expensive, and because a tweet
travels further than a post and takes the mistake with it.

- **Every number.** Sourceable, and would you name the source in the replies?
- **Every story.** Yours, and true the way it is written?
- **Anyone identifiable.** A client, an employer, a person you are describing
  without naming. Would they recognise themselves, and would they mind?

## Step 3: the screenshot test

Read it as though somebody who dislikes you has quoted it with one line above
it. This is not paranoia, it is the normal life of a tweet that travels.

You are looking for one thing: is there a reading of this that you did not
intend and cannot defend? If there is, decide deliberately whether to close it
or to accept it. Both are valid. Not noticing is not.

Being unable to defend it is different from being disagreed with. A tweet
people argue with is often working.

## Step 4: check what the length took out

A tweet gets cut to fit, and the first thing cut is usually the qualifier. That
is how a reasonable thought becomes an absolute claim.

Ask what was trimmed. If it was the word that made it true, the tweet is now
wrong and shorter, which is worse than long.

## Step 5: check it still sounds like you

Read it back for the tells: a register borrowed from whoever you read this
morning, a punchline structure that is not yours, hedging you do not use. Short
form makes borrowing easier and more obvious.

## Step 6: rank, then stop

At most three fixes, ordered by cost, plus which checks came back clean. Then
say plainly whether you would post it as it stands, and be willing to say yes.

## What this will not do

It will not tell you whether the tweet will perform. Timing, who sees it early
and what else is happening decide as much as the words do.

It also will not give you a number. Reading a draft against a handful of posts
you pasted is a read-through, not a measurement.

## What changes when VoiceMoat is connected

Steps 1 to 4 are craft. Step 5 is the one that needs to know you:

- `get_voice_profile` returns a profile trained on your own published posts,
  held separately for Twitter and for LinkedIn, so a tweet is never judged
  against how you write long form.
- `score_voice_match` scores the draft from 0 to 100 against that profile,
  with a note on what is off. This is where the audit stops being an opinion.
- `improve_post` takes it through a deeper pass when step 6 finds three real
  fixes rather than one.
- `publish_post` sends it once you are happy, behind a preview and a one-time
  confirmation.

Never make the second call on your own. Show the person the exact preview the
first call returns and wait for a clear yes before you send the one-time code
back. Never make both calls in one step.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
