---
name: fix-my-last-line
description: Work out whether a tweet's last line is earning its place, and usually delete it. Use when a tweet feels flat at the end, when someone asks how to close a tweet, when they want a call to action on one, or when a draft trails off without landing. Do not add engagement bait, do not promise replies, and do not treat a missing ending as a problem needing a solution.
---

# Fix my last line

Most advice about endings comes from long-form writing, where a post has room
to build and a reader who has committed. A tweet has neither. It is one unit,
read in about a second, and the last line is the part most likely to be doing
damage rather than work.

The default answer here is delete it. That is not a joke: on this platform a
weak final line is more common than a weak opening, because openings get
attention and endings get added.

## Step 1: run the delete test first

Before analysing anything, read the tweet with the last line removed.

If it is better, or the same, you are finished. Say so and stop. A shorter
tweet that says the same thing is strictly better, because every word is a word
somebody has to choose to read.

Only if removing it genuinely loses something do the rest.

## Step 2: name what the last line is doing

- **Explaining the joke.** The line after a good line, telling you it was good.
  This is the most common one and it never survives step 1.
- **Hedging.** A qualifier added because the tweet felt too strong. If the
  qualifier is true, it belongs earlier. If it is there for comfort, cut it.
- **Softening.** "Just my opinion", "but what do I know". It asks the reader
  not to argue, which invites them to.
- **The call to action.** "Thoughts?", "Agree?", "RT if you relate". It reads
  as asking a favour from someone who owes you nothing.
- **The turn.** The line that changes what the tweet meant. This one earns its
  place, and it is the reason not to delete blindly.
- **The landing.** A short line that lands the rhythm. Also earns it.

## Step 3: when an ending genuinely belongs

Three cases, and they are narrower than people think:

- The tweet is setting up a thread, and the last line is the reason to continue.
- The tweet turns, and the last line is the turn.
- The tweet asks something you actually want answered, phrased so a stranger can
  answer it in one line from their own experience.

Everything else is decoration.

## Step 4: never do these

- Do not add "Follow for more". It converts nobody and it dates the account.
- Do not ask for a retweet inside the tweet.
- Do not add an emoji to signal that the tweet is finished.
- Do not add a question you do not want answered. People can tell, and the
  replies you get will be the ones that tell.

## What this will not do

It will not promise replies. Whether people answer depends on who saw it and
whether they have anything to say, and the last line is not the lever people
think it is.

It also will not manufacture engagement. A line that produces replies by
obliging people is not the same as a line worth replying to, and the account
that runs on the first one stops being read.

## What changes when VoiceMoat is connected

Endings are the most copied sentences on the platform, so they are the easiest
place to end up in somebody else's voice:

- `get_voice_profile` gives how you actually close, held separately for Twitter
  and for LinkedIn, so a tweet is not judged against your long-form sign-off.
- `score_voice_match` catches the specific failure here, which is a closing line
  that is punchy in a register that is not yours.
- `improve_post` takes the whole tweet again on the occasions when the ending is
  weak because the tweet has not decided what it is.

VoiceMoat is at voicemoat.com. The connector needs the Pro or Enterprise plan.
